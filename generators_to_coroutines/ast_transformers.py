import ast
import inspect
import copy


class AnalyzeGeneratorFunction(ast.NodeVisitor):

    def __init__(self):
        self.loadedNames = set()
        # store statements that come after loops
        self.loopsToBeConverted = set()
        self.functionArguments = None
        self.target = None

    def visit_FunctionDef(self, node):
        """ Gather function arguments for use later. """
        if self.functionArguments is None:
            self.functionArguments = node.args.args

        self.generic_visit(node)

    def isForStatementCandidate(self, node):
        """ Return True if For statement is a candidate for transformation """

        return self.functionArguments is not None and \
            isinstance(node.iter, ast.Name) and \
            node.iter.id in (arg.id for arg in self.functionArguments)

    def visit_For(self, node):
        """ Change iteration into while-yield statements """

        if self.isForStatementCandidate(node):
            self.loopsToBeConverted.add(node)
            if self.target is not None:
                # TODO: raise exception if different target!
                pass
            else:
                # save the iterable, which will be now used as a target
                # instead.
                self.target = node.iter

        self.generic_visit(node)

    def visit_Name(self, node):

        if isinstance(node.ctx, ast.Load):
            self.loadedNames.add(node.id)

        self.generic_visit(node)

    def __str__(self):
        return "names = {}\n"\
               "loopsToBeConverted = {}\n"\
               "functionArgs = {}\n"\
               "target = {}".format(
                   self.loadedNames,
                   self.loopsToBeConverted,
                   map(astpp.dump, self.functionArguments),
                   astpp.dump(self.target))


class InvertGenerator(ast.NodeTransformer):
    """ Transform a function AST, from a generator into a coroutine (from pull
    to push). The iterable parameter to the generator that was pulled from, now
    becomes the "target" parameter of the coroutine that is pushed to."""

    def __init__(self):
        self.analysis = None
        self.loopsToBeWrapped = None

    def _tryExceptGeneratorExit(self, tryBody, exceptBody):
        """ Create a try-except wrapper around two bodies of statements. """
        return ast.TryExcept(
            body=tryBody,
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id='GeneratorExit', ctx=ast.Load()),
                    name=None,
                    body=exceptBody),
            ],
            orelse=[])

    def _moreValuesAvailableAssignmentNode(self, loadId):
        return ast.Assign(
            targets=[ast.Name(id=self.moreValuesAvailableId, ctx=ast.Store())],
            value=ast.Name(id=loadId, ctx=ast.Load()))

    def visit_FunctionDef(self, node):
        node.body.insert(0, self._moreValuesAvailableAssignmentNode('True'))
        return self.generic_visit(node)

    def visit(self, node):

        # perform analysis on whole AST as a first phase
        # (only called once)
        if self.analysis is None:
            self.analysis = AnalyzeGeneratorFunction()
            self.analysis.visit(node)
            self.loopsToBeWrapped = copy.copy(self.analysis.loopsToBeConverted)

            self.moreValuesAvailableId = "moreValuesAvailable"
            while self.moreValuesAvailableId in self.analysis.loadedNames:
                self.moreValuesAvailableId += str(random.randint(0, 1000000))

        return super(InvertGenerator, self).visit(node)

    def visit_For(self, node):
        """ Change iteration into while-yield statements """
        # TODO: take care of StopIteration conversion?

        newnode = node

        if node in self.analysis.loopsToBeConverted:
            # For(expr target, expr iter, stmt* body, stmt* orelse)
            # While(expr test, stmt* body, stmt* orelse)

            # prepend statement to await a value in the coroutine
            newbody = [ast.Assign(targets=[node.target],
                                  value=ast.Yield(value=None))] + node.body
            whileNode = ast.While(
                test=ast.Name(id=self.moreValuesAvailableId, ctx=ast.Load()),
                body=newbody,
                orelse=[])  # TODO: what to do with orelse

            newnode = self._tryExceptGeneratorExit(
                [whileNode],
                [self._moreValuesAvailableAssignmentNode('False')])

        self.generic_visit(newnode)

        return ast.copy_location(newnode, node)

    def _coroutineSendExpression(self, target, exprToSend):
        """ Create an expression like
            target.send(exprToSend)
        """
        return ast.Expr(value=ast.Call(
            func=ast.Attribute(
                value=target,
                attr='send',
                ctx=ast.Load()),
            args=[exprToSend],
            keywords=[],
            starargs=None,
            kwargs=None
            ))

    def _extractValueFromYieldExpr(self, expr):

        if isinstance(expr.value, ast.Yield):
            return expr.value.value

        return None

    def visit_Expr(self, node):

        newnode = node

        yieldValue = self._extractValueFromYieldExpr(node)
        if yieldValue is not None:
            newnode = self._coroutineSendExpression(
                self.analysis.target,
                yieldValue)

        self.generic_visit(newnode)
        return newnode


class RemoveDecorators(ast.NodeTransformer):

    def visit_FunctionDef(self, node):
        node.decorator_list = []
        return node

    def visit_ClassDef(self, node):
        node.decorator_list = []
        return node


def transformAstWith(globalEnv, transformers):
    """ Create a decorator that transforms functions in a given global
    environment, using the provided NodeTransformer classes """

    # Always remove decorators when transforming
    # TODO: necessary?
    transformers.insert(0, RemoveDecorators)

    def transformDecorator(func):
        funcName = func.__name__

        # TODO: need to unindent if method or local function
        node = ast.parse(inspect.getsource(func))

        #print "BEFORE: "
        #print astpp.dump(node)

        for transformer in transformers:
            node = transformer().visit(node)

        #print "AFTER: "
        #print astpp.dump(node)

        ast.fix_missing_locations(node)
        compiled = compile(node, '<string>', 'exec')

        tempNamespace = copy.copy(globalEnv)
        exec compiled in tempNamespace

        return tempNamespace[funcName]

    return transformDecorator

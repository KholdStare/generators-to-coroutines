import ast
import inspect
import copy
import six
import random
import sys
import textwrap


if sys.version_info[0] == 3 and sys.version_info[1] > 2:
    _TryNode = ast.Try
else:
    _TryNode = ast.TryExcept

if six.PY3:
    def getFunctionArgumentIdentifiers(node):
        return [arg.arg for arg in node.args.args]
else:
    def getFunctionArgumentIdentifiers(node):
        return [arg.id for arg in node.args.args]


class AnalyzeGeneratorFunction(ast.NodeVisitor):

    def __init__(self):
        # ids of all accessed variables, to aid in finding nonconflicting
        # identifiers
        self.loadedNames = set()

        self.loopsToBeConverted = set()
        # ids of all function arguments
        self.functionArgumentIds = None
        self.target = None

        # ids of variables used as iterators
        self.iteratorIdSet = set()

        # nodes that are unnecessary in coroutine
        self.nodesToBeDeleted = set()

        # "iterator.next()" calls to be converted to "(yield)"
        self.nextCallsToBeConverted = set()

    @classmethod
    def _doesCallHaveNoParameters(cls, callNode):
        return len(callNode.args) == 0 and \
            len(callNode.keywords) == 0 and \
            callNode.starargs is None and \
            callNode.kwargs is None

    @classmethod
    def _doesCallInvokeMethod(cls, methodName, callNode):
        return isinstance(callNode.func, ast.Attribute) and \
            callNode.func.attr == methodName and \
            isinstance(callNode.func.ctx, ast.Load)

    @classmethod
    def _doesCallGetIterator(cls, callNode):
        noParameters = cls._doesCallHaveNoParameters(callNode)
        iterCall = cls._doesCallInvokeMethod('__iter__', callNode)

        return iterCall and noParameters

    @classmethod
    def _extractObjectIdFromMethodCall(cls, callNode):
        if isinstance(callNode.func.value, ast.Name) and \
                isinstance(callNode.func.value.ctx, ast.Load):
            return callNode.func.value.id

    @classmethod
    def _doesCallGetNext(cls, callNode):
        noParameters = cls._doesCallHaveNoParameters(callNode)
        # deal with python 3 compatibility and six library
        nextCall = cls._doesCallInvokeMethod('next', callNode) or \
            cls._doesCallInvokeMethod('__next__', callNode)

        return nextCall and noParameters

    def visit_Call(self, node):
        """ check for expressions
            iterator.next()
        and remember the node """

        if self._doesCallGetNext(node):
            potentialIteratorId = self._extractObjectIdFromMethodCall(node)

            if potentialIteratorId in self.iteratorIdSet or \
                    potentialIteratorId in self.functionArgumentIds:
                self.nextCallsToBeConverted.add(node)

        self.generic_visit(node)

    def visit_Assign(self, node):
        """ check for statements like
            iterator = iterable.__iter__()
        and remember the iterator """

        if len(node.targets) == 1 and \
                isinstance(node.value, ast.Call) and \
                self._doesCallGetIterator(node.value):
            potentialIterableId = \
                self._extractObjectIdFromMethodCall(node.value)

            # TODO: perhaps not enough to just check function argument IDs
            # need to bundle the iterable it came from?
            if potentialIterableId in self.functionArgumentIds:
                self._saveTarget(ast.Name(
                    id=potentialIterableId,
                    ctx=ast.Load()))
                self.iteratorIdSet.add(node.targets[0].id)
                self.nodesToBeDeleted.add(node)

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """ Gather function arguments for use later. """
        if self.functionArgumentIds is None:
            self.functionArgumentIds = getFunctionArgumentIdentifiers(node)

        self.generic_visit(node)

    def isForStatementCandidate(self, node):
        """ Return True if For statement is a candidate for transformation """

        return self.functionArgumentIds is not None and \
            isinstance(node.iter, ast.Name) and \
            node.iter.id in self.functionArgumentIds

    def _saveTarget(self, iterableNode):
        if self.target is not None:
            if self.target.id != iterableNode.id:
                raise Exception(
                    "Two different iterables that are parameters to the "
                    "generator are used for pulling values. Cannot "
                    "convert to a Coroutine.")
        else:
            # save the iterable, which will be now used as a target
            # instead.
            self.target = iterableNode

    def visit_For(self, node):
        """ Change iteration into while-yield statements """

        if self.isForStatementCandidate(node):
            self.loopsToBeConverted.add(node)
            self._saveTarget(node.iter)

        self.generic_visit(node)

    def visit_Name(self, node):

        if isinstance(node.ctx, ast.Load):
            self.loadedNames.add(node.id)

        self.generic_visit(node)


class InvertGenerator(ast.NodeTransformer):
    """ Transform a function AST, from a generator into a coroutine (from pull
    to push). The iterable parameter to the generator that was pulled from, now
    becomes the "target" parameter of the coroutine that is pushed to."""

    def __init__(self):
        self.analysis = None
        self.loopsToBeWrapped = None

    def _tryExceptGeneratorExit(self, tryBody, exceptBody):
        """ Create a try-except wrapper around two bodies of statements. """
        return _TryNode(
            body=tryBody,
            handlers=[
                ast.ExceptHandler(
                    type=ast.Name(id='GeneratorExit', ctx=ast.Load()),
                    name=None,
                    body=exceptBody),
            ],
            orelse=[],
            finalbody=[])

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

            if self.analysis.target is None:
                raise Exception(
                    "Analysis did not find an iterable input to "
                    "the Generator. Conversion to a Coroutine cannot be done.")

            self.loopsToBeWrapped = copy.copy(self.analysis.loopsToBeConverted)
            self.moreValuesAvailableId = "moreValuesAvailable"
            while self.moreValuesAvailableId in self.analysis.loadedNames:
                self.moreValuesAvailableId += str(random.randint(0, 1000000))

        if node in self.analysis.nodesToBeDeleted:
            return ast.Pass()

        if node in self.analysis.nextCallsToBeConverted:
            return ast.Yield(value=None)

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


def transformAstWith(globalEnv, localEnv, transformers):
    """ Create a decorator that transforms functions in a given global
    environment, using the provided NodeTransformer classes """

    # Always remove decorators when transforming
    # TODO: necessary?
    transformers.insert(0, RemoveDecorators)

    def transformDecorator(func):
        funcName = func.__name__

        node = ast.parse(textwrap.dedent(inspect.getsource(func)))

        #print "BEFORE: "
        #print astpp.dump(node)

        for transformer in transformers:
            node = transformer().visit(node)

        #print "AFTER: "
        #print astpp.dump(node)

        ast.fix_missing_locations(node)
        compiled = compile(node, '<string>', 'exec')

        tempNamespace = copy.copy(localEnv)
        six.exec_(
            compiled,
            copy.copy(globalEnv),
            tempNamespace)

        return tempNamespace[funcName]

    return transformDecorator

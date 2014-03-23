import dis
import ast
import inspect
import astpp

def viewAst(obj):
    node = ast.parse(inspect.getsource(obj))
    print astpp.dump(node)

    return obj

def coroutine(func):
    def start(*args, **kwargs):
        g = func(*args, **kwargs)
        g.next()
        return g
    return start

def invertibleGenerator(func):
    """ Add a co method to func, that is the equivalent coroutine. """

    func.co = coroutine(transformAstWith(InvertGenerator)(func))
    return func

class InvertGenerator(ast.NodeTransformer):
    # TODO: should probably be a two-pass procedure:
    # 1. Find what argument to turn from iterable to target
    # 2. Carry out transformations
    #
    # This needs to be done, if first yield is before first use of iterable,
    # in which case this code won't know how to conver the yield statement

    def __init__(self):
        self.functionArguments = None
        self.iterable = None

    def visit_FunctionDef(self, node):
        """ Gather function arguments for use later. """
        if self.functionArguments is None:
            self.functionArguments = node.args.args

        self.generic_visit(node)

        return node


    def isForStatementCandidate(self, node):

        return self.functionArguments is not None and \
                isinstance(node.iter, ast.Name) and \
                node.iter.id in (arg.id for arg in self.functionArguments)

    def visit_For(self, node):
        """ Change iteration into while-yield statements """
        # TODO: take care of GeneratorExit handling.
        # TODO: take care of StopIteration conversion?

        newnode = node
        if self.isForStatementCandidate(node):
	    #| For(expr target, expr iter, stmt* body, stmt* orelse)
	    #| While(expr test, stmt* body, stmt* orelse)

            # save the iterable, which will be now used as a target instead.
            self.target = node.iter

            newbody = [ast.Assign(targets=[node.target],
                                value=ast.Yield(value=None))] + node.body
            newnode = ast.While(
                    test = ast.Name(id='True', ctx=ast.Load()),
                    body = newbody,
                    orelse = []) # TODO: what to do with orelse

        self.generic_visit(newnode)

        return ast.copy_location(newnode, node)

    def coroutineSendExpression(self, target, exprToSend):
        return ast.Expr(value=ast.Call(
                    func = ast.Attribute(
                            value = target,
                            attr = 'send',
                            ctx = ast.Load()),
                    args=[exprToSend],
                    keywords=[],
                    starargs=None,
                    kwargs=None
                    )
                )

    def extractValueFromYieldExpr(self, expr):

        if isinstance(expr.value, ast.Yield):
            return expr.value.value

        return None


    def visit_Expr(self, node):
        
        newnode = node

        yieldValue = self.extractValueFromYieldExpr(node)
        if yieldValue is not None:
            newnode = self.coroutineSendExpression(
                    self.target,
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

def transformAstWith(*args):

    transformers = list(args)
    transformers.insert(0, RemoveDecorators)

    def transformDecorator(func):
        funcName = func.__name__

        # TODO: need to unindent if method?
        node = ast.parse(inspect.getsource(func))

        #print "BEFORE: "
        #print astpp.dump(node)
        for transformer in  transformers:
            transformer().visit(node)

        #print "AFTER: "
        #print astpp.dump(node)

        ast.fix_missing_locations(node)
        compiled = compile(node, '<string>', 'exec')

        tempNamespace = {}
        exec compiled in tempNamespace

        func.__code__ = tempNamespace[funcName].__code__

        return func

    return transformDecorator
    

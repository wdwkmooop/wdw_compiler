# -*- coding: utf-8 -*-
# @Time    : 2020/3/27 12:06
# @Author  : WDW
# @File    : RE2NFA.py
'''
使用thompson算法构建nfa,首先分析语法树,自底向上构建nfa
例子  ab*(a|b)*
语法树为
     +
  +    *
a  *   |
   b  a b
构建语法树的算法是:
使用两个栈,一个存放符号+,*,(  一个存放子表达式对应的子树
扫描表达式,遇到符号入栈1,遇到字符入栈2.  (+表示连接)
理论上符号优先级  () > * > + > |   符号栈应该满足优先级递增.遇到右括号就一直出栈直到左括号出栈
括号比较特殊,左括号应该直接入栈,但是这会使得括号后面的符号无法入栈.所以,让括号优先级最低
出栈时,将运算结果放回栈2
这样可以构建一个树了.
例如对于a+b*+(a|b)*
最初:    读a:   读+     读b     读*
s1 :    s1 :    s1:+   s1:+    s1:+   *是一个单目运算符,遇到*时直接处理
s2 :    s2 :a   s2:a   s2:a,b   s2:a,b* 此时取出栈顶的子树,让*成为他的根节点
读+                                        读(
s1:+ 先让+出栈,构建对应子树后,后来的+入栈    s1:+(
s2:a+b*                                   s2:a+b*
读a          读|         读b          读)                    读*
s1:+(       s1:+(|      s1:+(|       s1:+ 处理符号直到(      s1:+
s1:a+b*,a   s2:a+b*,a   s2:a+b*,a,b  s2:a+b*,a|b            s2:a+b*,(a|b)*
读完后,s1还剩了一个符号+,对之处理得a+b*+(a|b)*的树


这里的过程本来可以简化的,比如可以直接搞出regex的后缀表达式,或者直接从语法树得到dfa.
由于本人很菜,所以只能搞出这样一个简陋的东西,之后会考虑支持[a-z]这样的操作
另外还需要转义字符,\\,\*这样的


'''

priority = {'?': 2, '*': 2, '(': -1, ')': -1, '`': 1, '|': 0}


def getlevel(c):  # 优先级
    return priority[c]


def isop(c):
    return c in {'*', '(', ')', '`', '|', '?'}


class treenode():
    def __init__(self, val=None, left=None, right=None):
        self.left = left
        self.right = right
        self.val = val


class tree():
    '''
    语法树
    '''

    def __init__(self, regex):
        print(regex)
        self.rawexp = regex
        self.regex = proprocess(regex)
        self.s1 = []
        self.s2 = []

    def getTree(self):
        l, i = len(self.regex), -1
        while i < l - 1:
            i += 1
            c = self.regex[i]
            # print(self.s1,self.s2,c)
            if c == '\\':
                i += 1
                self.escape_char(self.regex[i])
                continue
            if isop(c):
                if c == '(':
                    self.s1.append(c)
                    continue
                if c == ')':  # 括号有点特殊,需要特殊处理
                    while self.s1[-1] != '(':
                        self.connect(self.s1.pop())
                    self.s1.pop()
                    continue
                if not self.s1 or getlevel(c) > getlevel(self.s1[-1]):
                    self.s1.append(c)
                else:
                    while self.s1 and getlevel(self.s1[-1]) >= getlevel(c):
                        self.connect(self.s1.pop())
                    self.s1.append(c)
            else:
                self.s2.append(treenode(c))
        while self.s1:
            c = self.s1.pop()
            self.connect(c)
        return self.s2.pop()

    def connect(self, c):  # 连接节点
        newnode = treenode(c)
        if c == '*' or c == '?':
            oldnode = self.s2.pop()
            newnode.left = oldnode
        else:  # 这里的情况是 | +
            n1 = self.s2.pop()
            n2 = self.s2.pop()
            newnode.left = n1
            newnode.right = n2
        self.s2.append(newnode)

    def escape_char(self, c):  # 处理转义字符
        self.s2.append(treenode(c))


# _todo: 操,集合[],能不能实现了啊,操,你们这些狗,怎么跟狗一样
def proprocess(exp):
    #  或许会把表达式扩展,以支持更强大灵活的语法
    #  何时该加+?两个表达式的中间.两个表达式的中间,
    #  要么是字母,字母   加+
    #  要么是字母,符号   除了(都不用加+   a* a| a) a? a(
    #  要么是符号,字母   如果是单目运算符要加+了 (a  |a   *`a  ?`a
    #  要么是符号,符号   不加  *| *) |)  () |* )(
    def kuohao(exp):
        newexp = ""
        for c in exp:
            if c == '\\':
                continue
        exp = newexp

    # kuohao(exp)
    newexp = ""
    lastchar = None
    l, i = len(exp), -1
    while i < l - 1:
        i += 1
        c = exp[i]
        if lastchar == '\\':
            lastchar = '\\' + c
            newexp += c
            continue
        if c == '\\':  # 转义符号,先忽略
            if lastchar is None:
                newexp += c
            else:
                newexp += '`'
                newexp += c
            continue
        if lastchar is None:
            newexp += c
        elif not isop(lastchar):
            if c == '(' or not isop(c):
                newexp += '`'
            newexp += c
        else:
            if isop(c):
                if c == '(':
                    newexp += '`'
                newexp += c
            else:
                if lastchar == '*' or lastchar == '?':
                    newexp += '`'
                newexp += c
        lastchar = c
    return newexp


'''
下面是AST-->NFA的过程
'''


class nfaNode():
    def __init__(self, isend=False):  # 节点最多只有两条出边,且入边,要么一条或多条空边,要么一条非空边
        self.epsilon = set()  # ε边
        self.char = {}  # 非空边
        self.state = nfa.cnt  # 状态编号
        nfa.cnt += 1
        self.isend = isend
        nfa.pool.append(self)


class nfa():
    cnt = 0
    pool = []  # 状态池

    def __init__(self, startstate: nfaNode = None, endstate: nfaNode = None):
        self.startstate = startstate
        self.endstate = endstate

    def transit_table(self):  # 输出转换表
        print("开始状态:", self.startstate.state, "接收状态:", self.endstate.state)
        for node in nfa.pool:
            print("状态:", node.state, "空转移:", node.epsilon, "非空转移:", node.char)


def constructNFA(tree: treenode):
    c = tree.val
    start = nfaNode()
    end = nfaNode(isend=True)
    if not tree.left and not tree.right:
        start.char[c] = end.state
    elif c == '*':
        subnfa = constructNFA(tree.left)
        subnfa.endstate.isend = False
        subnfa.endstate.epsilon.add(subnfa.startstate.state)
        start.epsilon.add(end.state)
        start.epsilon.add(subnfa.startstate.state)
        subnfa.endstate.epsilon.add(end.state)
    elif c == '?':  # 直接加一条ε边
        subnfa = constructNFA(tree.left)
        subnfa.endstate.isend = False
        subnfa.endstate.epsilon.add(end.state)
        start.epsilon.add(end.state)
        start.epsilon.add(subnfa.startstate.state)
    elif c == '|':
        subnfa1 = constructNFA(tree.left)
        subnfa2 = constructNFA(tree.right)
        subnfa1.endstate.isend = False
        subnfa2.endstate.isend = False
        start.epsilon.add(subnfa1.startstate.state)
        start.epsilon.add(subnfa2.startstate.state)
        subnfa1.endstate.epsilon.add(end.state)
        subnfa2.endstate.epsilon.add(end.state)
    elif c == '`':  # 注意先后顺序哦,right是在前面的
        subnfa1 = constructNFA(tree.left)
        subnfa2 = constructNFA(tree.right)
        subnfa2.endstate.isend = False
        subnfa2.endstate.epsilon.add(subnfa1.startstate.state)
        start.epsilon.add(subnfa2.startstate.state)
        subnfa1.endstate.epsilon.add(end.state)
    return nfa(start, end)


def getnfa(re: str):
    t = tree(re)
    _t = t.getTree()
    ret = constructNFA(_t)
    # ret.endstate = [ret.endstate.state]
    return ret


def main():
    def houxu(t):
        if not t:
            return
        houxu(t.right)
        houxu(t.left)
        print(t.val, end="")
    re = '\\('
    tre = tree(re)
    # print(tre.regex)
    t = tre.getTree()
    print("begin"), houxu(t), print('')
    mynfa = getnfa(re)
    # my = constructNFA(t)
    mynfa.transit_table()
    print(mynfa.endstate.state)


if __name__ == "__main__":
    main()

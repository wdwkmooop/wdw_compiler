# -*- coding: utf-8 -*-
# @Time    : 2020/3/26 18:10
# @Author  : WDW
# @File    : nfa2dfa.py

'''
这里用子集构造法从nfa生成dfa
算法要计算三个函数:
ε-closure(s):nfa开始状态的ε闭包
ε-closure(T):可以从T中某个状态s开始只通过epsilon转换到达的状态集合
move(T,a):可以从T中某个状态s开始经过a边到达的状态集合

求ε-closure的方法是:
T中所有状态入栈
初始化epsilon-closure为T
不断出栈,将它们的空边对应节点,若不在epsilon-closure内,就加入,并入栈

计算DFA状态states和状态转移表trans的方法是:
初始化状态集合 states = {epsilon-closure(开始状态)}, visited = {}
当states中有没访问节点T,循环:
    visited[T] = True
    for all a:
        U = ε-closure( move(T,a) )
        if U not in states:
            states加入U
        trans[T,a] = U


考虑未来可能是多条正则表达式组合的nfa,也就是说有多个接受状态,DFA状态需要记住哪个接收态对应哪个表达式
一个DFA状态可能对应多个nfa接收态,可以让在前的状态优先匹配.例如(1,2,3),若2,3都是接收态,则认为串属于2代表的表达式
'''
import lex.RE2NFA as re2nfa


class DFA():
    cnt = 0

    def __init__(self, nfa: re2nfa.nfa):
        self.nfa = nfa
        self.states = set()
        self.trans = {}  # 双重字典,state,char->state 的映射
        self.startstate = None
        self.endstates = {}
    #  对于一个元素的元组,可要记着写成(1,)这样的形式
    def _epsilon_closure(self, T: tuple):  # 求出集合T的epsilon闭包,包含了单个状态s的epsilon闭包
        ret = set(T)
        stack = []
        for s in T:
            stack.append(s)

        while len(stack) != 0:
            s = stack.pop()
            for _s in self.nfa.pool[s].epsilon:
                if _s not in ret:
                    stack.append(_s)
                    ret.add(_s)
        return tuple(ret)

    def _move_set(self, T: tuple, a: str):  # 求move集合
        ret = set()
        for s in T:
            if a in self.nfa.pool[s].char:
                ret.add(self.nfa.pool[s].char[a])
        return tuple(ret)

    def minimize(self):
        assert 'not yet implement'
    def simplify(self):
        #  重新编号,方便人查看,也减少储存空间
        new_trans = {}
        new_endstates = {}
        i = 0
        rename = {}
        for _s in self.states:
            rename[_s] = i
            i += 1
        for k, v in self.trans.items():
            _t = {}
            for _k, _v in v.items():
                _t[_k] = rename[_v]
            new_trans[rename[k]] = _t
        for _s, _type in self.endstates.items():
            new_endstates[rename[_s]] = _type
        self.trans = new_trans
        self.endstates = new_endstates
        self.startstate = rename[self.startstate]
        self.curState = self.startstate




    def construct_DFA(self):
        '''
        todo: 按原计划构建好dfa,写一个数据结构存下多条表达式和它们对应的nfa状态号,以此简化dfa状态的表达,然后最小化.
        todo: 最后输出转换表,应该就可以识别标识符,关键字,常量了(字符串和注释还有问题,必须先实现 . 的功能)
        todo: 要实现.貌似有点讲究... 迫不得已可以加上[a-zA-Z0-9{}[]()]等的边,但太傻
        todo: 对边进行压缩,一条边代表一个字符集合... 这样也方便实现[0-9]这样的东西
        todo: 最后的想法就是,将原文件一行一行读进来(不考虑一条语句换行的情况),以空格切分,因为c语言里,空格切分的一定是
        todo: 不同的词素.扔到自动机里跑,当失配时就回退到最近状态,输出最前的nfa状态代表的表达式的token,剩下的接着跑
        todo: 啊对了,输出token时输出下行号和列号吧.
        todo: 至于异常处理,慢慢搞吧...
        :return:
        '''
        #  为了解决多条正则表达式匹配的问题,我决定记录每个nfa的终结状态及其对应的表达式,
        #  同时,dfa的状态中储存了nfa的状态.由此可以知道dfa的终结状态对应哪些表达式.优先级根据表达式的顺序实现
        #  最后对dfa进行最小化,去掉dfa状态元组中非终结状态的状态,让它没那么臃肿可怕.
        #  最终的结果dfa接受状态应该是O(正则表达式数量),比较友好了
        #  nfa只是一个中间过渡的产品.尽管nfa的物理表示不是一张表,依然可以构造DFA状态和转换表
        u = self._epsilon_closure((self.nfa.startstate.state,))
        self.startstate = u
        self.states.add(u)
        last = [u]  # last 是上一次循环扩展出的状态
        while True:
            if not last: break
            newlast = []
            for state in last:
                if state not in self.trans:
                    self.trans[state] = dict()
                charset = set()
                for _s in state:
                    charset |= self.nfa.pool[_s].char.keys()
                for c in charset:
                    u = self._epsilon_closure(self._move_set(state, c))
                    self.trans[state][c] = u
                    if u not in self.states:
                        self.states.add(u)
                        newlast.append(u)
                        #  是否接收状态
                        _ = self.nfa.endstate.keys() & set(u)
                        if len(_)!=0:
                            __ = min(_)
                            self.endstates[u] = self.nfa.endstate[__]
            last = newlast

    def match(self, word:str):
        # 让输入串在dfa上跑,失配时,返回上一个接收状态和失配位置
        l, i= len(word), 0
        curState = self.startstate
        while i<l:
            c = word[i]
            if c in self.trans[curState]:
                curState = self.trans[curState][c]
            else:
                return i, self.endstates[curState]

            i += 1
        return i, self.endstates[curState]


    def transit_table(self):
        print('开始状态:',self.startstate,'接收状态:',self.endstates)
        for s in self.trans:
            print(s)
            print(self.trans[s])


def getDFA(re: str):
    d = DFA(re2nfa.getnfa(re))
    d.construct_DFA()
    return d


#  这里传入正则表达式的时候一并传入对应的种别码type
#  在构造每个nfa时,记录对应的type,在合并为dfa时,记录对应的状态的type
#  优先级以type的大小体现,优先归类为最小的
def getDFA_from_multi(lis: list):
    # lis:list[(re,type)]
    temp_nfa = []
    ret = re2nfa.nfa(re2nfa.nfaNode(),None)
    ret.endstate = {}
    for item in lis:
        t = re2nfa.getnfa(item[0])
        temp_nfa.append(t)
        ret.endstate[t.endstate.state] = item[1]
    for nfa in temp_nfa:
        ret.startstate.epsilon.add(nfa.startstate.state)
    d = DFA(ret)
    d.construct_DFA()
    d.simplify()
    return d


def main():
    re = "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z"
    re2 = "A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z"
    #dfa = getDFA('0(x|X)(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*')
    #print(dfa.match('0x1233'))
    d = getDFA_from_multi([('(0|1|2|3|4|5|6|7|8|9)*',1),('int',2)])
    #d.simplify()
    d.transit_table()
    print(d.endstates)
if __name__ == '__main__':
    main()


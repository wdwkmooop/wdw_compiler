# -*- coding: utf-8 -*-
# @Time    : 2020/3/25 22:43
# @Author  : WDW
# @File    : lexer.py
import lex.RE2NFA as re2nfa
import lex.nfa2dfa as nfa2dfa

'''
先实现nfa到dfa,读取nfa表生成dfa表  maybe difficult
再实现dfa的算法,easy
根据正则表达式生成nfa可以以后再说

首先预处理一下
设计正则式
将正则式转换为dfa表
根据dfa表和自动机子程序,可以实现.
'''
'''
标识符:_letter(number|_letter)*
整数  = number+
浮点数 = number+.number*(e|E)?number+
字符串 = \" .*  \"
界符 = [\[\](){};,.=]
运算符 = [+-*/<>&|]|&&| \|\| |>=|<=|==|
注释 = /* .* */
'''

# 每个关键字可以构造一个正则表达式
key_word = ['int', 'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'long',
            'register', 'return', 'short', 'signed', 'sizeof', 'static', 'struct',
            'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while']
_board = [';', ',', '\\(', '\\)', '.', '{', '}', '[', ']', '=']
operater = ['==', '!=', '<=', '>=', '<', '>', '\\|\\|', '&&',
            '\\|', '&', '!', '++', '--', '\\*', '+', '-', '/']
identifier = '(_|a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|' \
             'A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z)' \
             '(0|1|2|3|4|5|6|7|8|9|' \
             '_|a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|' \
             'A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z)*'
integer = '(+|-)?(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*'
real = '(+|-)?(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*.(0|1|2|3|4|5|6|7|8|9)*(e|E)?' \
       '(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*'
_hex = '0(x|X)(0|1|2|3|4|5|6|7|8|9|a|b|c|d|e|f)(0|1|2|3|4|5|6|7|8|9|a|b|c|d|e|f)*'

regexs = []
regexs += [(x, 0) for x in key_word]
regexs += [(identifier, 1)]
regexs += [(x, 2) for x in _board]
regexs += [(x, 3) for x in operater]
regexs += [(integer, 4)]
regexs += [(real, 5)]
regexs += [(_hex, 6)]
#for x in regexs:
#    print(x)

class token():
    #  token形如<种别码,值>
    _type = {0: '关键字', 1: '标识符', 2: '界符', 3: '操作符', 4: '整数', 5: '浮点数', 6: '十六进制'}

    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def __str__(self):
        return '< ' + self._type[self.type] + ', ' + self.value + ' >'


class lexer():

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.dfa = nfa2dfa.getDFA_from_multi(regexs)
        self.source_code = ''
        self.row = 1
        self.col = 0
        f = open(self.filepath,encoding='utf-8')
        for s in f.readlines():
            self.source_code += s
        f.close()

    def match(self):
        l, i = len(self.source_code), 0
        while i<l:
            self.col += 1
            if self.source_code[i] in [' ', '\t', '\n']:
                if self.source_code[i] == '\n':
                    self.row += 1
                    self.col = 0
                i += 1
                continue
            if self.source_code[i] == '/':
                s = ''
                i += 1
                while i<l and self.source_code[i] != '/':
                    if self.source_code[i] == '\n':
                        self.row += 1
                        self.col = 0
                    s += self.source_code[i]
                    i += 1
                    self.col += 1
                if i==l: print('注释未完')
                i += 1
                print('<注释,_>')
                continue
            elif self.source_code[i] == '"':
                s = ''
                i += 1
                try:
                    while i < l and self.source_code[i] != '"':  # 我突然感觉处理转义字符可以写个公共方法了,艹
                        if self.source_code[i] == '\n':
                            i += 1
                            raise Exception
                        if self.source_code[i] == '\\':
                            s += self.source_code[i]
                            s += self.source_code[i + 1]
                            i += 2
                            continue
                        s += self.source_code[i]
                        i += 1
                except:
                    print('line %d, column %d: ' % (self.row, self.col), '未匹配的双引号')
                    self.row += 1
                if i == l:
                    print('line %d, column %d: ' % (self.row, self.col), '未匹配的双引号')
                    return
                i += 1
                print('<字符串常量,%s>' % s)
                continue
            else:
                begin = i
                cur_state = self.dfa.startstate
                accept_state = None
                while True:
                    c = self.source_code[i]
                    if c in self.dfa.trans[cur_state]:
                        cur_state = self.dfa.trans[cur_state][c]
                        if cur_state in self.dfa.endstates:
                            accept_state = (i+1,self.dfa.endstates[cur_state])
                    else:
                        if accept_state is not None:
                            print(token(accept_state[1],self.source_code[begin:accept_state[0]]))
                            i = accept_state[0]
                            break
                        else :
                            print('line %d, column %d: ' % (self.row, self.col), '无法识别的单词拼写')
                            i += 1
                            break
                    i += 1

def main():
    lex = lexer('code.c')
    # lex.dfa.transit_table()
    # lex.dfa.nfa.transit_table()
    # lex.dfa.transit_table()
    lex.match()


if __name__ == '__main__':
    main()


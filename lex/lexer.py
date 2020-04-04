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
integer = '(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*'
real = '(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*.(0|1|2|3|4|5|6|7|8|9)*(e|E)?' \
       '(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*'
_hex = '0(x|X)(0|1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*'

regexs = []
regexs += [(x, 0) for x in key_word]
regexs += [(identifier, 1)]
regexs += [(x, 2) for x in _board]
regexs += [(x, 3) for x in operater]
regexs += [(integer, 4)]
regexs += [(real, 5)]
regexs += [(_hex, 6)]
for x in regexs:
    print(x)

class token():
    #  token形如<种别码,值>
    _type = {0: '关键字', 1: '标识符', 2: '界符', 3: '操作符', 4: '整数', 5: '浮点数', 6: '十六进制'}

    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def __str__(self):
        return '<' + self._type[self.type] + ',' + self.value + '>'


class lexer():

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.dfa = nfa2dfa.getDFA_from_multi(regexs)

    def tokenize(self):
        f = open(self.filepath)
        self.row = 0  # 目前扫描到的行号
        while True:
            line = f.readline()
            if line == '': break
            self.row += 1
            self._tokenize_line(line)
        f.close()

    def _tokenize_line(self, line: str):
        l, i = len(line), 0
        while i < l:
            if line[i] in [' ', '\t', '\n']:
                i += 1
                continue
            if line[i] == '/':
                s = ''
                i += 1
                while line[i] != '/':
                    s += line[i]
                    i += 1
                i += 1
                print('<注释,_>')
                continue
            elif line[i] == '"':
                s = ''
                i += 1
                while line[i] != '"':  # 我突然感觉处理转义字符可以写个公共方法了,艹
                    if line[i] == '\\':
                        s += line[i]
                        s += line[i+1]
                        i += 2
                        continue
                    s += line[i]
                    i += 1
                i += 1
                print('<字符串常量,%s>' % s)
                continue
            else:
                # print(line[i:])
                try:
                    pos, _type = self.dfa.match(line[i:])
                    word = line[i:pos + i]
                    i += pos
                    print(token(_type, word))
                    continue
                except nfa2dfa.lexerror as e:
                    print('line %d, column %d: ' %(self.row,i),e )
                    i += e.i

def main():
    lex = lexer('code.c')
    # lex.dfa.transit_table()
    lex.tokenize()


if __name__ == '__main__':
    main()

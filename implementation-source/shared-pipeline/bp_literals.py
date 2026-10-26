"""Literal-only blueprint parsing and recursive merge checks; never executes Lua."""
import ast
import copy
import re

TOKEN = re.compile(r'''\s+|--\[\[.*?\]\]|--[^\n]*|\[\[.*?\]\]|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z_]\w*|[{}\[\]=,;]''', re.S)


class LiteralTable:
    def __init__(self, source):
        self.tokens = []
        pos = 0
        for m in TOKEN.finditer(source):
            if m.start() != pos:
                raise ValueError(f'Unsupported Lua syntax at offset {pos}')
            pos = m.end()
            text = m.group()
            if text.isspace() or text.startswith('--'):
                continue
            self.tokens.append(text)
        if pos != len(source):
            raise ValueError(f'Unsupported Lua syntax at offset {pos}')
        self.i = 0

    def take(self, expected=None):
        token = self.tokens[self.i]
        self.i += 1
        if expected is not None and token != expected:
            raise ValueError(f'Expected {expected}, found {token}')
        return token

    def value(self):
        token = self.take()
        if token == '{':
            result = {}
            index = 1
            while self.tokens[self.i] != '}':
                if self.tokens[self.i] == '[':
                    self.take('['); key = self.value(); self.take(']'); self.take('=')
                    value = self.value()
                elif self.i + 1 < len(self.tokens) and self.tokens[self.i + 1] == '=':
                    key = self.take(); self.take('='); value = self.value()
                else:
                    key = index; index += 1; value = self.value()
                if key in result:
                    raise ValueError(f'Duplicate table key: {key}')
                result[key] = value
                if self.tokens[self.i] in {',', ';'}:
                    self.take()
                elif self.tokens[self.i] != '}':
                    raise ValueError('Missing table field separator')
            self.take('}')
            return result
        if token.startswith(('\'', '"')):
            return ast.literal_eval(token)
        if token.startswith('[['):
            return token[2:-2]
        if token in {'true', 'false', 'nil'}:
            return {'true': True, 'false': False, 'nil': None}[token]
        if re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', token):
            return float(token) if any(c in token for c in '.eE') else int(token)
        raise ValueError(f'Unsupported literal: {token}')

    def blueprint(self):
        self.take('UnitBlueprint')
        result = self.value()
        if self.i != len(self.tokens):
            raise ValueError('Trailing Lua source after blueprint')
        return result


def merge(dest, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(dest.get(key), dict):
            merge(dest[key], value)
        else:
            dest[key] = copy.deepcopy(value)


def differences(before, after, path=''):
    changes = []
    for key in before.keys() | after.keys():
        here = f'{path}.{key}' if path else str(key)
        if key not in before or key not in after:
            changes.append(here)
        elif isinstance(before[key], dict) and isinstance(after[key], dict):
            changes.extend(differences(before[key], after[key], here))
        elif before[key] != after[key]:
            changes.append(here)
    return sorted(changes)

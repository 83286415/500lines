"""A simple Python template renderer, for a nano-subset of Django syntax."""

# Coincidentally named the same as http://code.activestate.com/recipes/496702/

import re


class TempliteSyntaxError(ValueError):
    """Raised when a template has a syntax error."""
    pass


class CodeBuilder(object):
    """Build source code conveniently."""

    def __init__(self, indent=0):
        self.code = []
        self.indent_level = indent

    def __str__(self):
        return "".join(str(c) for c in self.code)

    def add_line(self, line):
        """Add a line of source to the code.

        Indentation and newline will be added for you, don't provide them.

        """
        self.code.extend([" " * self.indent_level, line, "\n"])

    def add_section(self):
        """Add a section, a sub-CodeBuilder."""
        section = CodeBuilder(self.indent_level)
        self.code.append(section)
        return section

    INDENT_STEP = 4      # PEP8 says so!

    def indent(self):
        """Increase the current indent for following lines."""
        self.indent_level += self.INDENT_STEP

    def dedent(self):
        """Decrease the current indent for following lines."""
        self.indent_level -= self.INDENT_STEP

    def get_globals(self):
        """Execute the code, and return a dict of globals it defines."""
        # A check that the caller really finished all the blocks they started.
        assert self.indent_level == 0
        # Get the Python source as a single string.
        python_source = str(self)
        # Execute the source, defining globals, and return them.
        global_namespace = {}
        exec(python_source, global_namespace)
        return global_namespace


class Templite(object):
    """A simple template renderer, for a nano-subset of Django syntax.

    Supported constructs are extended variable access::

        {{var.modifer.modifier|filter|filter}}

    loops::

        {% for var in list %}...{% endfor %}

    and ifs::

        {% if var %}...{% endif %}

    Comments are within curly-hash markers::

        {# This will be ignored #}

    Construct a Templite with the template text, then use `render` against a
    dictionary context to create a finished string::

        templite = Templite('''
            <h1>Hello {{name|upper}}!</h1>
            {% for topic in topics %}
                <p>You are interested in {{topic}}.</p>
            {% endif %}
            ''',
            {'upper': str.upper},
        )
        text = templite.render({
            'name': "Ned",
            'topics': ['Python', 'Geometry', 'Juggling'],
        })

    """
    def __init__(self, text, *contexts):
        """Construct a Templite with the given `text`.

        `contexts` are dictionaries of values to use for future renderings.
        These are good for filters and global values.

        """
        self.context = {}
        for context in contexts:
            self.context.update(context)

        self.all_vars = set()  # 所有模板类中使用的变量在这个set中，如上例中的user_name
        self.loop_vars = set()	 # 所有模板中定义的变量在这个set中，如上例中的product.name，在它的循环中定义的。

        # We construct a function in source form, then compile it and hold onto
        # it, and execute it to render the template.
        code = CodeBuilder()

        code.add_line("def render_function(context, do_dots):")
        code.indent()
        vars_code = code.add_section()  # another code builder instance
        code.add_line("result = []")
        code.add_line("append_result = result.append")  # one line adds
        code.add_line("extend_result = result.extend")	 # more lines add
        code.add_line("to_str = str")

        buffered = []

        def flush_output():
            """Force `buffered` to the code builder."""
            if len(buffered) == 1:
                code.add_line("append_result(%s)" % buffered[0])
            elif len(buffered) > 1:
                code.add_line("extend_result([%s])" % ", ".join(buffered))
            del buffered[:]

        ops_stack = []

        # Split the text to form a list of tokens.
        tokens = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text)

        for token in tokens:
            if token.startswith('{#'):
                # Comment: ignore it and move on. 略过注释
                continue
            elif token.startswith('{{'):
                # An expression to evaluate. 变量
                expr = self._expr_code(token[2:-2].strip())
                # 去掉双大括号后，将里面是string变为python的表达式expr
                buffered.append("to_str(%s)" % expr)
                # to_str(expr)是个函数被str化
            elif token.startswith('{%'):
                # Action tag: split into words and parse further.
                flush_output()  # 在写入codebuilder实例前，清缓存
                words = token[2:-2].strip().split()  # 去掉{% %}
                if words[0] == 'if':
                    # An if statement: evaluate the expression to determine if.
                    if len(words) != 2:  # 只验证变量是否存在的true or false
                        self._syntax_error("Don't understand if", token)
                    ops_stack.append('if')  # 将if加入ops列表，之后还有endif要加入
                    code.add_line("if %s:" % self._expr_code(words[1]))
                    code.indent()  # if从句下面 +4 indent
                elif words[0] == 'for':
                    # A loop: iterate over expression result.
                    if len(words) != 4 or words[2] != 'in':
                        self._syntax_error("Don't understand for", token)
                    ops_stack.append('for')
                    self._variable(words[1], self.loop_vars)
                    # 加入word[1]合法，将其加入到loop_vars的set()中
                    code.add_line(
                        "for c_%s in %s:" % (
                            words[1],
                            self._expr_code(words[3])
                        )  # 将for从句加入到code builder的实例中
                    )
                    code.indent()  # for从句以下的内容，indent + 4
                elif words[0].startswith('end'):
                    # Endsomething.  Pop the ops stack.
                    if len(words) != 1:  # endif or endfor
                        self._syntax_error("Don't understand end", token)
                    end_what = words[0][3:]  # what是if或者for
                    if not ops_stack:  # 之前有end，所以列表被pop空了
                        self._syntax_error("Too many ends", token)
                    start_what = ops_stack.pop()
                    if start_what != end_what:  # 必须是if==if 或者 for==for
                        self._syntax_error("Mismatched end tag", end_what)
                    code.dedent()  # 从句完成后，缩进 - 4
                else:
                    self._syntax_error("Don't understand tag", words[0])
            else:
                # Literal content.  If it isn't empty, output it.
                if token:  # 例如带<p><li>标签的文字内容，直接输出
                    buffered.append(repr(token))  # repr为token加“”
        if ops_stack:  # miss了一个end tag
            self._syntax_error("Unmatched action tag", ops_stack[-1])
        flush_output()

        for var_name in self.all_vars - self.loop_vars:
            # 在all而不在loop中的，即所有在模板类中用到的，而不是在模板类中定义的。见all_vars
            # 因为在模板中定义的，如product.name已经在翻译时(在循环中)定义过；其他的需要真正定义一次。
            vars_code.add_line("c_%s = context[%r]" % (var_name, var_name))  # 定义

        code.add_line("return ''.join(result)")  # def render_function的return
        code.dedent()  # 针对def那个indent而有的dedent

        self._render_function = code.get_globals()['render_function']
        # run code and return a dict[render_function]

    def _expr_code(self, expr):
        """Generate a Python expression for `expr`."""
        if "|" in expr:
            pipes = expr.split("|")
            code = self._expr_code(pipes[0])
            for func in pipes[1:]:
                self._variable(func, self.all_vars)
                code = "c_%s(%s)" % (func, code)  # 将管道中的函数编程c_xxx,如c_lower(obj)
        elif "." in expr:
            dots = expr.split(".")
            code = self._expr_code(dots[0])
            args = ", ".join(repr(d) for d in dots[1:])
            code = "do_dots(%s, %s)" % (code, args)  # 将html中的a.b编程python的a.b
        else:
            self._variable(expr, self.all_vars)
            code = "c_%s" % expr
        return code

    def _syntax_error(self, msg, thing):
        """Raise a syntax error using `msg`, and showing `thing`."""
        raise TempliteSyntaxError("%s: %r" % (msg, thing))  # 这里的ERROR类就是pass

    def _variable(self, name, vars_set):
        """Track that `name` is used as a variable.

        Adds the name to `vars_set`, a set of variable names.

        Raises an syntax error if `name` is not a valid name.

        """
        if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", name):
            self._syntax_error("Not a valid name", name)
        vars_set.add(name)  # 模板中的每个变量都会加入到这个set中

    def render(self, context=None):
        """Render this template by applying it to `context`.

        `context` is a dictionary of values to use in this rendering.

        """
        # Make the complete context we'll use.
        render_context = dict(self.context)   # self本来就是dict
        if context:
            render_context.update(context)
        return self._render_function(render_context, self._do_dots)  # 这个self._render_function是html汇编成python的

    def _do_dots(self, value, *dots):  # 传进渲染函数的第二个参数是_do_dots
        """Evaluate dotted expressions at runtime."""
        for dot in dots:  # 如x.y.z则循环成x.y和x.z
            try:
                value = getattr(value, dot)  # 将x.y或x.z的值给value，不是给x
            except AttributeError:
                value = value[dot]  # 若是字典，则把x[y或z]的值给value，不是给x
            if callable(value):  # 若果value可悲调用，则返回True
                value = value()
        return value   # 返回的是调用函数或者属性值

from markdownify import markdownify as md

text = """
<a href="https://www.grandmasrecipes.fun/media/tasks/poetry_4yCcHQZ.jpg">​​​​​​</a>
<h2>Заголовок 2</h2>
<p>просто текст</p>
<p><strong>жирный текст</strong></p>
<p><i>курсив</i></p>
<ol>
<li>ли число 1</li>
<li>ли число 2</li>
</ol>
"""

print(md(text, strong_em_symbol='_'))

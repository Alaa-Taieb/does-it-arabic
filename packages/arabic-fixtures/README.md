# arabic-fixtures

Eight RTL test strings for document and image rendering, the same ones used by the Does It Arabic? matrix:
connected letterforms, lam-alef, harakat, a mixed bidi invoice line, Arabic-Indic and Persian digits,
Persian letters with ZWNJ, Hebrew with numbers, and line wrapping. Each fixture has `id`, `text`, `dir`,
`lang`, an English `meaning` and a plain-language `checks` description of what correct output looks like.

```js
const fx = require('arabic-fixtures');
fx.get('invoice-line').text; // 'Order #1234 للعميل محمد – 250 TND'
```

```python
import arabic_fixtures as fx
fx.get("invoice-line")["text"]
```

Not published to npm or PyPI yet. Node: `npm install ./packages/arabic-fixtures`. Python: put this folder
on `sys.path` (or copy `arabic_fixtures.py` and `fixtures.json` side by side). Data is CC0.

# arabic-fixtures

Eight right-to-left test strings for checking that your PDFs, OG images and charts render Arabic, Persian and
Hebrew correctly. They are the fixtures behind [Does It Arabic?](https://github.com/Alaa-Taieb/does-it-arabic),
a screenshot-backed test matrix of PDF, image and chart libraries.

| id | what it catches |
|---|---|
| `connected` | letters drawn isolated instead of joined |
| `lam-alef` | missing mandatory لا ligature |
| `harakat` | vowel marks dropped, floating or misplaced |
| `invoice-line` | `Order #1234 للعميل محمد – 250 TND`: mixed Arabic, Latin and numbers in bidi order |
| `digits` | Arabic-Indic (١٢٣) and Persian (۶۷۸) digits |
| `persian` | Persian ی ک پ گ and the zero-width non-joiner |
| `hebrew` | Hebrew with numbers |
| `wrapping` | line wrapping of an RTL paragraph |

Each fixture has `id`, `title`, `text`, `dir`, `lang`, an English `meaning` and `checks`, a plain-language
description of what correct output looks like.

## JavaScript

```bash
npm install arabic-fixtures
```

```js
const fx = require('arabic-fixtures');
fx.get('invoice-line').text;   // 'Order #1234 للعميل محمد – 250 TND'
fx.ids();                       // ['connected', 'lam-alef', ...]
```

## Python

```bash
pip install arabic-fixtures
```

```python
import arabic_fixtures as fx
fx.get("invoice-line")["text"]
fx.ids()
```

## Judging the output

Render a fixture with your code. The image or PDF page should contain only that text. Then judge it with the
`check` command from the [Does It Arabic? repository](https://github.com/Alaa-Taieb/does-it-arabic#check-your-own-output):

```bash
python -m doesitarabic check invoice.pdf --fixture invoice-line --font YourFont.ttf
```

## Licence

The fixtures are released under CC0 1.0 (public domain). Made by [Alaa Taieb](https://github.com/Alaa-Taieb).

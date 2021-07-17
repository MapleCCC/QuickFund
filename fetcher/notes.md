QUESTION: do we need to specify default value for fields? Have a trial and
see what happens if we construct a dataclass without parameters while the
dataclass contains fields that have no default values.
ANSWER: Turn out that we can't. Try attrs library or try to use a sentinel to
signal MISSING VALUE.

QUESTION: can we dynamically create new property to a dataclass instance?
ANSWER: Yes.
WORKAROUND: Add __slots__ property, or use attrs library.
Turn out that it's been a infamous problem that there is no simple good way to
incorporate dataclass and slots. So we are left with using attrs library.
Or we can use @add_slots decorator by ericvsmith.

QUESTION: can we assign value to a field that doesn't match the type
annotation?
ANSWER: Yes. Type annotation doesn't impose runtime restriction, except a
few minor situations. We should rely on static type checker to maintain the type
restriction in code editing time.
WORKAROUND: Use pydantic instead.

QUESTION: what happen if workbook.add_format({})? Will we get a default cell format, like
what we get when calling workbook.add_format()? What about
workbook.add_format(None)?
ANSWER: Judging from source code of the XlsxWriter library, add_format({}) and
add_format(None) is equivalent to default format.

QUESTION: Does dataclass support __getitem__?
ANSWER: No.

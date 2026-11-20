"""Public links accept a confirmed Telegram address and bot username."""
import json
import re

from configure_telegram import public_configuration, validate

group, bot = validate('https://t.me/EmplivoGroup', '@EmplivoApplyBot')
for enabled in (False, True):
    output = public_configuration(group, bot, enabled)
    actual = json.loads(re.search(r'Object\.freeze\((\{.*?\})\);', output, re.S)[1])
    assert actual == {'groupUrl': group, 'botUsername': bot, 'botEnabled': enabled}
for invalid in ('https://example.org/t.me/EmplivoGroup', 'javascript:alert(1)', 'https://t.me/Group?token=secret'):
    try:
        validate(invalid, bot)
    except ValueError:
        pass
    else:
        raise AssertionError(invalid)
print('PASS: public Telegram config and address validation')

# -*- coding: utf-8 -*-
import sync_bitable_fields_v2 as s

token = s.get_access_token()
print(f'Token: {token[:20]}...')

# Sync one bitable
print('\n--- Running sync_single_bitable for lifeos_jin ---')
result = s.sync_single_bitable('DtWnbquyZaIj9xsWLSIcagjQnAc', '金 - LifeOS', token)
print(f'\nResult: {result}')

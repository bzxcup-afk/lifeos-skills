# -*- coding: utf-8 -*-
import sync_bitable_fields_v2 as s

token = s.get_access_token()
print(f'Token: {token[:20]}...')

# List tables
print('\nListing tables for lifeos_jin...')
tables = s.list_tables('DtWnbquyZaIj9xsWLSIcagjQnAc', token)
print(f'Found {len(tables)} tables:')
for t in tables:
    print(f'  {t["name"]}: {t["table_id"]}')

# Sync
print('\n--- Running sync_single_bitable ---')
result = s.sync_single_bitable('DtWnbquyZaIj9xsWLSIcagjQnAc', '金 - LifeOS', token)
print(f'\nResult: {result}')

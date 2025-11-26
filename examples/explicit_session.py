"""Explicit session management example."""

from phoebe_client import PhoebeClient

client = PhoebeClient(host="localhost", port=8001)

try:
    session = client.start_session()
    print(f"Session ID: {session['session_id']}")

    client.set_value(qualifier='period', component='binary', kind='orbit', context='component', value=2.5)
    result = client.get_bundle()

    if result.get('success'):
        bundle = result['result']['bundle']
        with open('my_bundle.phoebe', 'w') as f:
            f.write(bundle)

finally:
    client.end_session()

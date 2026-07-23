import frida, time, sys

mgr = frida.get_device_manager()
devices = mgr.enumerate_devices()
socket_dev = [d for d in devices if d.id == 'socket'][0]

print('Waiting for gadget to come online...')
for i in range(30):
    try:
        procs = socket_dev.enumerate_processes()
        if procs:
            print('GADGET_CONNECTED: %d processes' % len(procs))
            for p in procs[:5]:
                print('  %s (pid=%d)' % (p.name, p.pid))
            game_pid = None
            for p in procs:
                if 'tmgp' in p.name.lower() or 'delta' in p.name.lower():
                    game_pid = p.pid
                    break
            if game_pid:
                print('Game pid=%d, attaching...' % game_pid)
                session = socket_dev.attach(game_pid)
                script = session.create_script('console.log("Gadget is alive!");')
                script.load()
                print('SUCCESS: Frida gadget is working!')
                break
            break
    except Exception as e:
        msg = str(e)[:80]
        print('  Attempt %d: %s' % (i+1, msg))
    time.sleep(2)
print('Done')

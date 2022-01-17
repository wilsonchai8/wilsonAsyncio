import wilsonasyncio

async def hello():
    print('enter hello ...')
    return 'return hello ...'

async def world():
    print('enter world ...')
    return 'return world ...'

async def helloworld():
    print('enter helloworld')
    ret = await wilsonasyncio.gather(hello(), world())
    print('exit helloworld')
    return ret

    
if __name__ == "__main__":
    ret = wilsonasyncio.run(helloworld())
    print(ret)

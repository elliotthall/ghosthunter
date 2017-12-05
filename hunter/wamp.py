from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

"""
WAMP GhostHunt client protocols
Elliott Hall 4/12/2017


"""

class HunterComponent(ApplicationSession):
    hunter = None

    """
    Autobahn WAMP component to communicate with 
    
    Ghost Hunt WAMP server protocols
    """
    def __init__(self, config=None, hunter=None):
        ApplicationSession.__init__(self, config)
        if hunter:
            self.hunter = hunter
        print("component created")

    def onConnect(self):
        print("transport connected")
        self.join(self.config.realm)

    def onChallenge(self, challenge):
        print("authentication challenge received")

    def onJoin(self, details):
        print("session joined")
        # can do subscribes, registers here e.g.:
        # await self.subscribe(...)
        # await self.register(...)

    def onLeave(self, details):
        print("session left")

    def onDisconnect(self):
        print("transport disconnected")
class CatchPokemon:
    def __init__(self, arguments):
        self.arguments = arguments

    def tick(self, bot):
        print 'checking if pokemon are visible'
        print 'picking pokemon to catch'
        print ('catching pokemon'
 								'with greatballs greater than {} cp'
 								' and ultraballs greater than {} cp'
 							).format(self.arguments['greatBallCP'], self.arguments['ultraBallCP'])
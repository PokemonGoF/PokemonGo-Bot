class TransferPokemon:
    def __init__(self, arguments):
        self.arguments = arguments
        print arguments

    def tick(self, bot):
        print ("transfering pokemon with a"
        				"minimum of {} CP so that we have {} slots left"
        			).format(self.arguments['minimumCP'], self.arguments['minimumRemainingSlots'])
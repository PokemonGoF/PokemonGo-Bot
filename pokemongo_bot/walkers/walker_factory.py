from pokemongo_bot.walkers.polyline_walker import PolylineWalker
from pokemongo_bot.walkers.step_walker import StepWalker

def walker_factory(name, bot, dest_lat, dest_lng, dest_alt=None, *args, **kwargs):
    '''
    Charlie and the Walker Factory
    '''
    if 'StepWalker' == name:
        ret = StepWalker(bot, dest_lat, dest_lng, dest_alt)
    elif 'PolylineWalker' == name:
        mode = "walking"
        if "mode" in kwargs:
            mode = kwargs["mode"]
        ret = PolylineWalker(bot, dest_lat, dest_lng, mode=mode)
    return ret

import random

from pokemongo_bot import logger
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.human_behaviour import sleep



class CompleteTutorial(BaseTask):

    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.api = self.bot.api
        self.nickname = self.config.get('nickname','')
        self.team = self.config.get('team',0)
        self.may_run = True

    def should_run(self):
        return self.may_run

    def work(self):

        if not self.should_run():
            return WorkerResult.SUCCESS

        # Only execute the worker once to avoid error loop
        self.may_run = False

        if self._check_tutorial_state():
            return WorkerResult.SUCCESS
        else:
            return WorkerResult.ERROR

    def _check_tutorial_state(self):
        self._player=self.bot.player_data

        tutorial_state = self._player.get('tutorial_state', [])
        # LEGAL_SCREEN = 0
        if not 0 in tutorial_state:
            sleep(2)
            if self._set_tutorial_state(0):
                self.logger.info('Completed legal screen')
                tutorial_state = self._player.get('tutorial_state', [])
            else:
                return False

        # AVATAR_SELECTION = 1
        if not 1 in tutorial_state:
            sleep(7)
            if self._set_avatar():
                if self._set_tutorial_state(1):
                    self.logger.info('Completed avatar selection')
                    tutorial_state = self._player.get('tutorial_state', [])
                else:
                    return False
            else:
                self.logger.error('Error during avatar selection')
                return False

        # POKEMON_CAPTURE = 3
        if not 3 in tutorial_state:
            sleep(10)
            if self._encounter_tutorial():
                self.logger.info('Completed first capture')
            else:
                self.logger.error('Error during first capture')
                return False

        # NAME_SELECTION = 4
        if not 4 in tutorial_state:
            if not self.nickname:
                self.logger.info("No nickname defined in config")
                return False

            self.logger.info(u'Trying to set {} as nickname'.format(self.nickname))
            sleep(5)
            if self._set_nickname(self.nickname):
                self._set_tutorial_state(4)
                tutorial_state = self._player.get('tutorial_state', [])
            else:
                self.logger.error('Error trying to set nickname')
                return False

        # FIRST_TIME_EXPERIENCE_COMPLETE = 7
        if not 7 in tutorial_state:
            if self._set_tutorial_state(7):
                self.logger.info('Completed first time experience')
            else:
                return False

        return True

    def _encounter_tutorial(self):
        # You just need to call the API with the pokemon you choose
        # Probably can't get MewTwo as first pokemon though
        first_pokemon_id = random.choice([1, 4, 7])
        response_dict = self.api.encounter_tutorial_complete(
            pokemon_id=first_pokemon_id)
        try:
            if response_dict['responses']['ENCOUNTER_TUTORIAL_COMPLETE']['result'] == 1:
                return True
            else:
                self.logger.error("Error during encouter tutorial")
                return False
        except KeyError:
            self.logger.error("KeyError during encouter tutorial")
            return False

    def _random_avatar(self):
        avatar= {}
        # 0 = Male, 1 = Female
        avatar['gender']=random.randint(0,1)
        # What is the max value of each parameter ?
        # Default is 0, anyway human player will stop
        # at the first choices in general, so fully
        # random on the whole avatar space is not the way to go either
        avatar['skin']=random.randint(0,3)
        avatar['hair']=random.randint(0,3)
        avatar['shirt']=random.randint(0,3)
        avatar['pants']=random.randint(0,3)
        avatar['hat']=random.randint(0,3)
        avatar['shoes']=random.randint(0,3)
        avatar['eyes']=random.randint(0,3)
        avatar['backpack']=random.randint(0,3)
        return avatar

    def _set_avatar(self):
        avatar = self._random_avatar()
        response_dict = self.api.set_avatar(player_avatar=avatar)
        status = response_dict['responses']['SET_AVATAR']['status']
        try:
            if status == 1:
                return True
            else:
                error_codes = {
                    0: 'UNSET',
                    1: 'SUCCESS',
                    2: 'AVATAR_ALREADY_SET',
                    3: 'FAILURE',
                }
                self.logger.error("Error during avatar selection : {}".format(error_codes[status]))
                return False
        except KeyError:
            self.logger.error("KeyError during avatar selection")
            return False

    def _set_nickname(self, nickname):
        response_dict = self.api.claim_codename(codename=nickname)
        try:
            result = response_dict['responses']['CLAIM_CODENAME']['status']
            if result == 1:
                self.logger.info(u'Name changed to {}'.format(nickname))
                return True
            else:
                # Would be nice to get the text directly from the proto Enum
                error_codes = {
                    0: 'UNSET',
                    1: 'SUCCESS',
                    2: 'CODENAME_NOT_AVAILABLE',
                    3: 'CODENAME_NOT_VALID',
                    4: 'CURRENT_OWNER',
                    5: 'CODENAME_CHANGE_NOT_ALLOWED'
                }
                self.logger.error(
                    u'Error while changing nickname : {}'.format(error_codes[result]))
                return False
        except KeyError:
            return False

    def _set_tutorial_state(self, completed):
        response_dict = self.api.mark_tutorial_complete(tutorials_completed=[
                                                        completed], send_marketing_emails=False, send_push_notifications=False)
        try:
            self._player = response_dict['responses'][
                'MARK_TUTORIAL_COMPLETE']['player_data']
            return response_dict['responses']['MARK_TUTORIAL_COMPLETE']['success']
        except KeyError:
            self.logger.error("KeyError while setting tutorial state")
            return False

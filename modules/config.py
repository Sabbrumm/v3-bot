from paths import CONFIG_PATH
import configparser
import json

class Config():
    _config = configparser.ConfigParser()
    def __init__(self):
        self._config.read(CONFIG_PATH)

        self.bot_token = self._config['BotInit']['bot_token']
        self.group_id = int(self._config['BotInit']['group_id'])
        self.bot_dev_name = self._config['BotInit']['bot_dev_name']
        self.bot_name = self._config['BotInit']['bot_name']

        self.global_boost = int(self._config['BoostVars']['global_boost'])
        self.global_ups = int(self._config['BoostVars']['global_ups'])
        self.global_likes = int(self._config['BoostVars']['global_likes'])
        self.max_posts_per_boost = int(self._config['BoostVars']['max_posts_per_boost'])

        self.checking_peers = json.loads(self._config['Peers']['checking_peers'])
        self.main_peers = json.loads(self._config['Peers']['main_peers'])

        self.max_captchas = int(self._config['BoostConf']['max_captchas'])
        self.search_delay_min = int(self._config['BoostConf']['search_delay_min'])
        self.search_delay_max = int(self._config['BoostConf']['search_delay_max'])
        self.uplike_delay_min = int(self._config['BoostConf']['uplike_delay_min'])
        self.uplike_delay_max = int(self._config['BoostConf']['uplike_delay_max'])
        self.watch_delay_min = int(self._config['BoostConf']['watch_delay_min'])
        self.watch_delay_max = int(self._config['BoostConf']['watch_delay_max'])
        self.good_post_likes = int(self._config['BoostConf']['good_post_likes'])
        self.good_post_views = int(self._config['BoostConf']['good_post_views'])
        self.good_post_count = int(self._config['BoostConf']['good_post_count'])
        self.posts_per_load = int(self._config['BoostConf']['posts_per_load'])

        self.ad_alert_times = json.loads(self._config['TimeBinds']['ad_alert_times'])
        self.alert_times = json.loads(self._config['TimeBinds']['alert_times'])
        self.drop_times = json.loads(self._config['TimeBinds']['drop_times'])
        self.post_reset_times = json.loads(self._config['TimeBinds']['post_reset_times'])

        self.pin_boost_message = int(self._config['BotBehaviour']['pin_boost_message'])
        self.status_only_for_admins = int(self._config['BotBehaviour']['status_only_for_admins'])
        self.post_reset_after_drop = int(self._config['BotBehaviour']['post_reset_after_drop'])
        self.new_user_posts = int(self._config['BotBehaviour']['new_user_posts'])
        self.delete_post_messages = int(self._config['BotBehaviour']['delete_post_messages'])

    def update_config(self):
        self._config['BotInit']['bot_token'] = str(self.bot_token)
        self._config['BotInit']['group_id'] = str(self.group_id)
        self._config['BotInit']['bot_dev_name'] = str(self.bot_dev_name)
        self._config['BotInit']['bot_name'] = str(self.bot_name)

        self._config['BoostVars']['global_boost'] = str(self.global_boost)
        self._config['BoostVars']['global_ups'] = str(self.global_ups)
        self._config['BoostVars']['global_likes'] = str(self.global_likes)
        self._config['BoostVars']['max_posts_per_boost'] = str(self.max_posts_per_boost)

        self._config['Peers']['checking_peers'] = str(self.checking_peers)
        self._config['Peers']['main_peers'] = str(self.main_peers)

        self._config['BoostConf']['max_captchas'] = str(self.max_captchas)
        self._config['BoostConf']['search_delay_min'] = str(self.search_delay_min)
        self._config['BoostConf']['search_delay_max'] = str(self.search_delay_max)
        self._config['BoostConf']['uplike_delay_min'] = str(self.uplike_delay_min)
        self._config['BoostConf']['uplike_delay_max'] = str(self.uplike_delay_max)
        self._config['BoostConf']['watch_delay_min'] = str(self.watch_delay_min)
        self._config['BoostConf']['watch_delay_max'] = str(self.watch_delay_max)
        self._config['BoostConf']['good_post_likes'] = str(self.good_post_likes)
        self._config['BoostConf']['good_post_views'] = str(self.good_post_views)
        self._config['BoostConf']['good_post_count'] = str(self.good_post_count)
        self._config['BoostConf']['posts_per_load'] = str(self.posts_per_load)

        self._config['TimeBinds']['ad_alert_times'] = json.dumps(self.ad_alert_times)
        self._config['TimeBinds']['alert_times'] = json.dumps(self.alert_times)
        self._config['TimeBinds']['drop_times'] = json.dumps(self.drop_times)
        self._config['TimeBinds']['post_reset_times'] = json.dumps(self.post_reset_times)

        self._config['BotBehaviour']['pin_boost_message'] = str(self.pin_boost_message)
        self._config['BotBehaviour']['status_only_for_admins'] = str(self.status_only_for_admins)
        self._config['BotBehaviour']['post_reset_after_drop'] = str(self.post_reset_after_drop)
        self._config['BotBehaviour']['new_user_posts'] = str(self.new_user_posts)
        self._config['BotBehaviour']['delete_post_messages'] = str(self.delete_post_messages)

        with open(CONFIG_PATH, 'w') as configfile:
            self._config.write(configfile)
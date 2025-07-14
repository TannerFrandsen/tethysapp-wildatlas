from tethys_sdk.base import TethysAppBase
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting


class App(TethysAppBase):
    """
    Tethys app class for Wild Atlas.
    """
    name = 'Wild Atlas'
    description = 'Interactive Wildlife tracker '
    package = 'wildatlas'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.svg'
    root_url = 'wildatlas'
    color = '#2980b9'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def persistent_store_settings(self):
        """
        Define Persistent Store Settings.
        """
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='primary_db',
                description='primary database',
                initializer='wildatlas.models.init_primary_db',
                required=True
            ),
        )

        return ps_settings

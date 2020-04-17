# _*_ coding:utf-8 _*_
# __Author__： zizle
from flask import Blueprint

from .views import OnDutyView, FileHandlerOnDutyMsgView, RetrieveOnDutyView

onduty_blp = Blueprint(name='onduty', import_name=__name__, url_prefix='/')
onduty_blp.add_url_rule('onduty-message/', view_func=OnDutyView.as_view(name='ondutymsg'))
onduty_blp.add_url_rule('onduty-message/<int:rid>/', view_func=RetrieveOnDutyView.as_view(name='rtvondutymsg'))
onduty_blp.add_url_rule('onduty-message/file/', view_func=FileHandlerOnDutyMsgView.as_view(name="ondf"))

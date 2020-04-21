# Author: zizle
from flask import Blueprint

from .views import ArticlePublishView, RetrieveArticlePublishView, ArticlePublishExportView

"""
文章发表记录功能模块
"""

article_publish_blp = Blueprint(name='artplb', import_name=__name__, url_prefix='/')
article_publish_blp.add_url_rule('article-publish/', view_func=ArticlePublishView.as_view(name="apush"))
article_publish_blp.add_url_rule('article-publish/<int:rid>/', view_func=RetrieveArticlePublishView.as_view(name="revapush"))
article_publish_blp.add_url_rule('article-publish/export/', view_func=ArticlePublishExportView.as_view(name="revapushexport"))



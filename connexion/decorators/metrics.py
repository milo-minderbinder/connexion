
import functools
import os
import time

from connexion.decorators.produces import BaseSerializer

try:
    import uwsgi_metrics
    HAS_UWSGI_METRICS = True
except ImportError:
    uwsgi_metrics = None
    HAS_UWSGI_METRICS = False


class UWSGIMetricsCollector:
    def __init__(self, path, method):
        self.path = path
        self.method = method
        swagger_path = path.strip('/').replace('/', '.').replace('<', '{').replace('>', '}')
        self.key_suffix = '{method}.{path}'.format(path=swagger_path, method=method.upper())
        self.prefix = os.getenv('HTTP_METRICS_PREFIX', 'connexion.response')

    @staticmethod
    def is_available():
        return HAS_UWSGI_METRICS

    def __call__(self, function):
        """
        :type function: types.FunctionType
        :rtype: types.FunctionType
        """

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            status_code = 500
            start_time_s = time.time()
            try:
                response = function(*args, **kwargs)
                _, status_code, _ = BaseSerializer.get_full_response(response)
            finally:
                end_time_s = time.time()
                delta_s = end_time_s - start_time_s
                delta_ms = delta_s * 1000
                key = '{status}.{suffix}'.format(status=status_code, suffix=self.key_suffix)
                uwsgi_metrics.timer(self.prefix, key, delta_ms)
            return response

        return wrapper

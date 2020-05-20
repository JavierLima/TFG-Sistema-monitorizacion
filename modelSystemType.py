import json
import types


class MetricsValidator:
    def __init__(self, path_model_validator):

        self.__path_model_validator = path_model_validator

        with open(path_model_validator, 'r') as json_file:
            self.__model_validator = json.load(json_file)

        self.__types_permitted = {
            "float": float,
            "int": int,
            "str": str
        }

    def verify_metrics(self, system_type, metrics):
        for metric in self.__model_validator[system_type]:

            if metric not in metrics:
                print("[*] No concuerda el modelo con las métricas recibidas, no tiene la métrica %s" % metric)
                raise NameError("[*] No concuerda el modelo con las métricas recibidas, no tiene la métrica %s" % metric)

            if type(self.__model_validator[system_type][metric]) is list:
                for elem in metrics[metric]:
                    for key, value in elem.items():
                        metric_type = self.__get_type(self.__model_validator[system_type][metric][0][key])
                        try:
                            elem[key] = metric_type(elem[key])
                        except TypeError:
                            raise TypeError("[*] No es del tipo adecuado la métrica %s el campo %s - tipo esperado %s" % (metric, key, self.__model_validator[system_type][metric][0][key]))
            else:
                for key, value in self.__model_validator[system_type][metric].items():
                    metric_type = self.__get_type(value)
                    try:
                        metrics[metric][key] = metric_type(metrics[metric][key])
                    except TypeError:
                        raise TypeError("[*] No es del tipo adecuado la métrica %s el campo %s - tipo esperado %s" % (metric, key, value))

        return metrics

    def __get_type(self, type_string):
        return self.__types_permitted[type_string]

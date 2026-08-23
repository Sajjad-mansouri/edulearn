from django.db import models


class SequentialField(models.IntegerField):
    """
    Automatically assigns sequential numbers to new instances.
    """

    def pre_save(self, model_instance, add):
        if add:
            max_val = model_instance.__class__.objects.aggregate(
                max_val=models.Max(self.attname)
            )["max_val"]

            if max_val is None:
                value = 1

            else:
                value = max_val + 1

            setattr(model_instance, self.attname, value)
            return value
        else:
            return getattr(model_instance, self.attname)

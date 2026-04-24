from django.db import models

class MessaggioDato(models.Model):
    canale = models.IntegerField(default=0)
    ADC = models.IntegerField(default=0)
    ToT = models.IntegerField(default=0)

    def __str__(self):
        return f"CH{self.canale} : ADC {self.ADC}, ToT {self.ToT}"
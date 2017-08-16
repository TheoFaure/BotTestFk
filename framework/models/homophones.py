from django.db import models


class Homophone(models.Model):
    def __str__(self):
        return self.word_set.values().__str__()


class Word(models.Model):
    word = models.CharField(max_length=30)
    homophone = models.ForeignKey(Homophone, on_delete=models.CASCADE)
    def __str__(self):
        return self.word

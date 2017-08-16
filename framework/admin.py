from django.contrib import admin
from .models.models import *
from .models.homophones import *


admin.site.register(Utterance)
admin.site.register(Answer)
admin.site.register(Intent)
admin.site.register(Entity)
admin.site.register(Mutant)
admin.site.register(Strategy)
admin.site.register(Validation)
admin.site.register(Homophone)
admin.site.register(Word)
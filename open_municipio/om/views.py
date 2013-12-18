from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.views.generic.base import TemplateView
from open_municipio.acts.models import Calendar, Act, ActSupport
from open_municipio.events.models import Event
from open_municipio.locations.models import Location
from open_municipio.newscache.models import News
from open_municipio.people.models import municipality, InstitutionResponsability, Person
from open_municipio.taxonomy.models import Category, Tag
from open_municipio.users.views import extract_top_monitored_objects

from django import http
from django.template import (Context, loader)
from open_municipio.votations.models import Votation
from django.contrib.sites.models import Site


def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context: None
    """
    c = Context({
        'STATIC_URL':settings.STATIC_URL,
        'main_city': settings.SITE_INFO['main_city'],
        'main_city_website': settings.SITE_INFO['main_city_website'],
    })

    t = loader.get_template(template_name) # You need to create a 500.html template.
    return http.HttpResponseServerError(t.render(c))

class HomeView(TemplateView):
    template_name = "om/home.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(HomeView, self).get_context_data(**kwargs)

        # get last two calendar events

        context['events'] = Event.future.all().order_by('date')[0:2]

#        context['last_presented_acts'] = Act.objects.\
#            filter(actsupport__support_type=ActSupport.SUPPORT_TYPE.first_signer).distinct().\
#            order_by('-actsupport__support_date')[0:3]

        context['last_presented_acts'] = Act.objects.\
            filter(presentation_date__isnull=False).distinct().\
            order_by('-presentation_date')[0:3]


        news = News.objects.filter(news_type=News.NEWS_TYPE.community, priority=1)
        context['last_community_news'] = sorted(news, key=lambda n: n.news_date, reverse=True)[0:3]

        context['key_acts'] = Act.objects.filter(is_key=True).order_by('-presentation_date')[0:3]
        context['key_votations'] = Votation.objects.filter(is_key=True).order_by('-sitting__date')[0:3]


        context['top_monitored'] = extract_top_monitored_objects(Person, qnt=3)

        try:
            context['most_acts'] = municipality.council.as_institution.charge_set.\
                filter(actsupport__support_type=ActSupport.SUPPORT_TYPE.first_signer).\
                annotate(n_acts=Count('actsupport')).order_by('-n_acts')[0:3]
        except ObjectDoesNotExist:
            # city council not exists
            context['most_acts'] = []

        # fetch most or least
        try:
            counselors = municipality.council.charges.select_related().order_by('person__last_name')
            context['most_rebellious'] = counselors.order_by('-n_rebel_votations')[0:3]
            context['most_trustworthy'] = counselors.order_by('n_rebel_votations')[0:3]
            context['least_absent'] = counselors.extra(select={'perc_absences':'(n_absent_votations * 100.0)/(n_absent_votations + n_present_votations)'}).order_by('perc_absences')[0:3]
        except ObjectDoesNotExist:
            # city council not present
            counselors = ()
            context['most_rebellious'] = ()
            context['most_trustworthy'] = ()
            context['least_absent'] = ()

        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        locations = list(Location.objects.all())

        context['tags_to_cloud'] = set(categories + tags + locations)
        context['current_site'] = Site.objects.get(pk=settings.SITE_ID)


        return context

    

class ContactsView(TemplateView):
    template_name = "om/contatti.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ContactsView, self).get_context_data(**kwargs)

        context["contacts_email"] = settings.CONTACTS_EMAIL
        
        return context


class ConditionsView(TemplateView):
    template_name = "om/terms-and-conditions.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ConditionsView, self).get_context_data(**kwargs)

        context["contacts_email"] = settings.CONTACTS_EMAIL
        
        return context



class PrivacyView(TemplateView):
    template_name = "om/privacy.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PrivacyView, self).get_context_data(**kwargs)

        context["webmaster_info"] = settings.WEBMASTER_INFO
        
        return context



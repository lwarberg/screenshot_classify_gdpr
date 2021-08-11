from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .models import Screenshot
from .models import Response
from .models import Task
from .models import Profile
from django.shortcuts import render
import re


@login_required
def index(request):
    # Get Navigation Destination
    navigate = request.POST.get('index_navigate')

    # Navigate to Task
    if navigate == 'Classify Screenshots':
        return HttpResponseRedirect('/classify')

    if navigate == 'Review Screenshots':
        return HttpResponseRedirect('/review')

    if navigate == 'Logout':
        logout(request)
        return HttpResponseRedirect('/')

    if navigate == 'Change Password':
        return HttpResponseRedirect('/accounts/password_change/')

    # Retrieve or Create User Profile
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Create Profile
        profile = Profile()
        profile.user = request.user
        profile.save()

        # Assign a Task
        assign_task(profile)

    num_tasks_completed = profile.assigned_tasks.count()

    if profile.setting_collaborative_sort:
        # Get Tasks that No Users have Completed
        num_tasks_remaining = len(Task.objects.filter(profile__user=None))
    else:
        # Get Tasks that Current User has Not Completed
        num_tasks_remaining = len(Task.objects.exclude(profile__user=profile.user))

    num_further_review = len(Screenshot.objects.filter(response__further_review=True).distinct())

    context = {'username': request.user.first_name,
               'tasks_completed': str(num_tasks_completed),
               'tasks_remaining': str(num_tasks_remaining),
               'furtherreview': str(num_further_review),
               'collaborativesort_checked': 'checked' if profile.setting_collaborative_sort else '',
               }
    return render(request, 'screenshot_app/index.html', context)


@login_required
def view(request, screenshot_id):
    # Retrieve or Create User Profile
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Create Profile
        profile = Profile()
        profile.user = request.user

    # Get Navigation Destination
    navigate = request.POST.get('task_navigate')

    # Return Home
    if navigate == 'home':
        return HttpResponseRedirect('/')

    # Default Behavior
    else:
        # Set Context
        request.session['previous_screenshot'] = Screenshot.objects.get(wave_id=3, country='USA', view_id=13434,
                                                                        channel_id='2a0de56c31f45c0c9cc714c7e4b861f9')
        request.session['session_context'] = {}

        return HttpResponseRedirect('/display/' + screenshot_id)


@login_required
def random(request, username):
    import random

    # Select User from Username
    target_user = User.objects.get(username=username)

    # Get Navigation Destination
    navigate = request.POST.get('task_navigate')

    # Get Next Screenshot and Record Response
    if navigate == 'next':
        # Get Form Data
        channel_id = request.POST.get('channel_id')
        view_id = int(request.POST.get('view_id'))
        wave_id = int(request.POST.get('wave_num'))
        country = request.POST.get('country')

        # Get Current Screenshot
        current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                    channel_id=channel_id)

        # Save Response from Request
        save_response(request, current_screenshot, request.user)

        # Select All Screenshot Responses from User
        responses = Response.objects.filter(user=target_user)

        # Select a Random Response
        response = random.choice(responses.all())

        # Get Next Screenshot from Response
        next_screenshot = response.screenshot

        request.session['previous_screenshot'] = current_screenshot

    if navigate == 'previous':

        # Get Form Data
        channel_id = request.POST.get('channel_id')
        view_id = int(request.POST.get('view_id'))
        wave_id = int(request.POST.get('wave_num'))
        country = request.POST.get('country')

        # Get Current Screenshot
        current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                    channel_id=channel_id)

        request.session['previous_screenshot'] = current_screenshot

        # Get Previous Screenshot from Session Variables
        try:
            next_screenshot = request.session['previous_screenshot']
        except:
            context = {'message': 'No Previous Screenshot Available'}
            return render(request, 'screenshot_app/error.html', context)

    if navigate is None:
        # Select All Screenshot Responses from User
        responses = Response.objects.filter(user=target_user)

        # Select a Random Response
        response = random.choice(responses.all())

        # Get Next Screenshot from Response
        next_screenshot = response.screenshot

    # Set Session Variables
    request.session['session_context'] = {'fillprevious_button_text': 'Fill ' + username + '\'s Response'}

    # Build Screenshot Parameters
    screenshot_parameters = str(next_screenshot.wave_id) + '_' + next_screenshot.country + '_' + \
                            str(next_screenshot.view_id) + '_' + next_screenshot.channel_id
    return HttpResponseRedirect('/random/' + username + '/' + screenshot_parameters)


@login_required
def classify(request):
    # Retrieve or Create User Profile
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Create Profile
        profile = Profile()
        profile.user = request.user

        # Assign a Task
        assign_task(profile)

    # Get Navigation Destination
    navigate = request.POST.get('task_navigate')

    # Get Next Screenshot and Record Response
    if navigate == 'next':

        # Get Form Data
        channel_id = request.POST.get('channel_id')
        view_id = int(request.POST.get('view_id'))
        wave_id = int(request.POST.get('wave_num'))
        country = request.POST.get('country')

        # Get Current Screenshot
        try:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                    channel_id=channel_id)
        except Screenshot.MultipleObjectsReturned:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                        channel_id=channel_id, batch_num=2)

        # Save Response from Request
        save_response(request, current_screenshot, request.user)

        # Get Next Screenshot
        next_screenshot = get_task_screenshot(profile, 'next', current_screenshot)

        if next_screenshot is None:
            context = {'message': 'No Screenshots Remaining'}
            return render(request, 'screenshot_app/error.html', context)
        else:
            screenshot = next_screenshot

        # Get Previous Screenshot
        previous_screenshot = get_task_screenshot(profile, 'previous', next_screenshot)

        if previous_screenshot is None:
            previous_screenshot = current_screenshot
            # context = {'message': 'Previous Screenshot Not Found'}
            # return render(request, 'screenshot_app/error.html', context)

    # Get Previous Screenshot
    if navigate == 'previous':

        # Get Form Data
        channel_id = request.POST.get('channel_id')
        view_id = int(request.POST.get('view_id'))
        wave_id = int(request.POST.get('wave_num'))
        country = request.POST.get('country')

        # Get Screenshot
        try:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                    channel_id=channel_id)
        except Screenshot.MultipleObjectsReturned:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                        channel_id=channel_id, batch_num=2)

        # Get Previous Screenshot
        previous_screenshot = get_task_screenshot(profile, 'previous', current_screenshot)

        if previous_screenshot is None:
            context = {'message': 'Previous Screenshot Not Found'}
            return render(request, 'screenshot_app/error.html', context)
        else:
            screenshot = previous_screenshot

    # Return Home
    if navigate == 'home':
        return HttpResponseRedirect('/')

    # Default Behavior
    if navigate is None:
        # Get Next Screenshot
        next_screenshot = get_task_screenshot(profile, 'next', None)

        if next_screenshot is None:
            context = {'message': 'No Screenshots Remaining'}
            return render(request, 'screenshot_app/error.html', context)
        else:
            screenshot = next_screenshot

        # Get Previous Screenshot
        previous_screenshot = get_task_screenshot(profile, 'previous', next_screenshot)

        if previous_screenshot is None:
            previous_screenshot = next_screenshot
            # context = {'message': 'Previous Screenshot Not Found'}
            # return render(request, 'screenshot_app/error.html', context)

    # Gather Summary Information
    num_tasks_completed = profile.assigned_tasks.count()

    if profile.setting_collaborative_sort:
        # Get Tasks that No Users have Completed
        num_tasks_remaining = len(Task.objects.filter(profile__user=None))
    else:
        # Get Tasks that Current User has Not Completed
        num_tasks_remaining = len(Task.objects.exclude(profile__user=profile.user))

    # Get Task to which Screenshot Belongs
    parent_task = Task.objects.get(screenshots__exact=screenshot)
    wave_total = parent_task.screenshots.count()

    if parent_task.screenshots.first() == screenshot:
        session_context = {
            'fillprevious_button': 'hidden',
            'task_num': num_tasks_completed,
            'task_total': num_tasks_remaining,
            'wave_total': wave_total,
        }
    else:
        session_context = {
            'task_num': num_tasks_completed,
            'task_total': num_tasks_remaining,
            'wave_total': wave_total,
            'fillprevious_button_text': 'Fill Previous Response',
        }

    # Set Session Variables
    request.session['session_context'] = session_context
    request.session['previous_screenshot'] = previous_screenshot

    # Build Screenshot Parameters
    screenshot_parameters = str(screenshot.wave_id) + '_' + screenshot.country + '_' + \
                            str(screenshot.view_id) + '_' + screenshot.channel_id
    return HttpResponseRedirect('/classify/' + screenshot_parameters)


@login_required
def review(request, username):
    # Retrieve or Create User Profile
    try:
        Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        context = {'message': 'Profile Does Not Exist'}
        return render(request, 'screenshot_app/error.html', context)

    # Get Navigation Destination
    navigate = request.POST.get('task_navigate')

    # Set Target User
    try:
        target_user = User.objects.get(username=username)
    except:
        context = {'message': 'Target User Not Found'}
        return render(request, 'screenshot_app/error.html', context)

    # Get Screenshots Marked for Further Review from Target User
    try:
        further_review_screenshots = Screenshot.objects.filter(response__user=target_user,
                                                               response__further_review=True)
    except:
        context = {'message': 'No Responses Marked for Review by User'}
        return render(request, 'screenshot_app/error.html', context)

    # Split Responses into Reviewed and Unreviewed
    try:
        reviewed_screenshots = further_review_screenshots.filter(response__user=request.user)
        unreviewed_screenshots = further_review_screenshots.exclude(response__user=request.user)
    except:
        context = {'message': 'Error Splitting Screenshots into Reviewed and Unreviewed'}
        return render(request, 'screenshot_app/error.html', context)

    if navigate == 'next':

        # Get Form Data
        channel_id = request.POST.get('channel_id')
        view_id = int(request.POST.get('view_id'))
        wave_id = int(request.POST.get('wave_num'))
        country = request.POST.get('country')

        # Get Current Screenshot
        try:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                    channel_id=channel_id)
        except Screenshot.MultipleObjectsReturned:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                        channel_id=channel_id, batch_num=2)

        # Save Response from Request
        save_response(request, current_screenshot, request.user)

        # Get Next Screenshot
        if unreviewed_screenshots.all().__len__() > 0:
            # Get First Unreviewed Screenshot
            next_screenshot = unreviewed_screenshots.first()

        else:
            context = {'message': 'No screenshots left to review'}
            return render(request, 'screenshot_app/error.html', context)

        # Set Previous Screenshot
        previous_screenshot = current_screenshot

    if navigate == 'previous':

        # Get Form Data
        channel_id = request.POST.get('channel_id')
        view_id = int(request.POST.get('view_id'))
        wave_id = int(request.POST.get('wave_num'))
        country = request.POST.get('country')

        # Get Current Screenshot
        try:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                    channel_id=channel_id)
        except Screenshot.MultipleObjectsReturned:
            current_screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id,
                                                        channel_id=channel_id, batch_num=2)

        # Get Previous Screenshot from Session Variables
        try:
            next_screenshot = request.session['previous_screenshot']
        except:
            context = {'message': 'No Previous Screenshot Available'}
            return render(request, 'screenshot_app/error.html', context)

        # Set Previous Screenshot
        previous_screenshot = current_screenshot

    if navigate is None:

        # Select Screenshot to Review
        if unreviewed_screenshots.all().__len__() > 0:
            # Get First Unreviewed Screenshot
            next_screenshot = unreviewed_screenshots.first()

            # Set Previous Screenshot
            if reviewed_screenshots.all().__len__() > 0:
                previous_screenshot = reviewed_screenshots.last()
            else:
                previous_screenshot = None

        else:
            # Check if Any Screenshots Have Been Reviewed
            if reviewed_screenshots.all().__len__() > 0:
                # Get Last Reviewed Screenshot
                next_screenshot = reviewed_screenshots.last()

                # Set Previous Screenshot
                try:
                    previous_screenshot = reviewed_screenshots.all().order_by('-id')[1]
                except:
                    previous_screenshot = None
            else:
                context = {'message': 'No screenshots to review'}
                return render(request, 'screenshot_app/error.html', context)

    if navigate == 'home':
        return HttpResponseRedirect('/')

    # Set Session Variables
    request.session['session_context'] = {'fillprevious_button_text': 'Fill ' + username + '\'s Response'}
    request.session['previous_screenshot'] = previous_screenshot

    # Build Screenshot Parameters
    screenshot_parameters = str(next_screenshot.wave_id) + '_' + next_screenshot.country + '_' + \
                            str(next_screenshot.view_id) + '_' + next_screenshot.channel_id
    return HttpResponseRedirect('/review/' + username + '/' + screenshot_parameters)


@login_required
def display_screenshot(request, screenshot_id, username=None):
    # Parse Screenshot ID
    screenshot_parameters = screenshot_id.split('_')
    wave_id = int(screenshot_parameters[0])
    country = screenshot_parameters[1]
    view_id = screenshot_parameters[2]
    channel_id = screenshot_parameters[3]

    # Set Target User and Endpoint
    if username is None:
        target_user = request.user
        endpoint = re.findall('(?<=\/)[a-z]+(?=\/)', request.path)[0]
    else:
        target_user = User.objects.get(username=username)
        endpoint = re.findall('(?<=\/)[a-z]+(?=\/)', request.path)[0] + '/' + username

    # Get Screenshot to Display
    try:
        screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id, channel_id=channel_id)
    except Screenshot.MultipleObjectsReturned:
        screenshot = Screenshot.objects.get(wave_id=wave_id, country=country, view_id=view_id, channel_id=channel_id,
                                            batch_num=2)
    except Screenshot.DoesNotExist:
        context = {'message': 'Screenshot Does Not Exist'}
        return render(request, 'screenshot_app/error.html', context)

    # Search if Response Already Exists for CURRENT USER (Not Target User)
    try:
        response = Response.objects.get(screenshot=screenshot, user=request.user)
        existing_context = {
            'category_nonotice_checked': 'checked' if response.category == 'nonotice' else '',
            'category_blankpage_checked': 'checked' if response.category == 'blankpage' else '',
            'category_blockeuusers_checked': 'checked' if response.category == 'blockeuusers' else '',
            'category_cookiewall_checked': 'checked' if response.category == 'cookiewall' else '',
            'category_notice_checked': 'checked' if response.category == 'notice' else '',
            'presentation_obst_checked': 'checked' if response.presentation == 'obst' else '',
            'presentation_banner_checked': 'checked' if response.presentation == 'banner' else '',
            'actions_accept_checked': 'checked' if response.actions_accept else '',
            'actions_decline_checked': 'checked' if response.actions_decline else '',
            'actions_moreinfo_checked': 'checked' if response.actions_more_information else '',
            'actions_settings_checked': 'checked' if response.actions_settings else '',
            'actions_close_checked': 'checked' if response.actions_close else '',
            'actions_privacypolicy_checked': 'checked' if response.actions_privacy_policy else '',
            'actions_preferencecheckboxes_checked': 'checked' if response.actions_preference_checkboxes else '',
            'content_trackingcookies_checked': 'checked' if response.content_tracking_cookies else '',
            'content_othercookies_checked': 'checked' if response.content_other_cookies else '',
            'content_acceptdefault_checked': 'checked' if response.content_default_accept else '',
            'content_implieddecline_checked': 'checked' if response.content_implied_decline else '',
            'content_explicitdecline_checked': 'checked' if response.content_explicit_decline else '',
            'content_preselectedcheckboxes_checked': 'checked' if response.content_preselected_checkboxes else '',
            'website_adblockerpresent_checked': 'checked' if response.website_adblocker_present else '',
            'website_subscriptionoption_checked': 'checked' if response.website_subscription_option else '',
            'website_paywallpresent_checked': 'checked' if response.website_paywall_present else '',
            'website_notactive_checked': 'checked' if response.website_not_active else '',
            'furtherreview_checked': 'checked' if response.further_review else '',
            'furtherreview_language_checked': 'checked' if response.further_review_language else 'false',
            'furtherreview_language_select': response.further_review_language_select,
            'furtherreview_other_checked': 'checked' if response.further_review_other else 'false',
            'furtherreview_other_text': response.further_review_other_text,
        }
    except Response.DoesNotExist:
        existing_context = {}

    # Get Previous Screenshot
    try:
        previous_screenshot = request.session['previous_screenshot']
    except:
        context = {'message': 'Previous Screenshot Not Found'}
        return render(request, 'screenshot_app/error.html', context)

    # Create Context from Previous Response
    try:
        if username:
            previous_response = Response.objects.get(screenshot=screenshot, user=target_user)
        else:
            previous_response = Response.objects.get(screenshot=previous_screenshot, user=target_user)
        previous_context = {
            'previous_category': previous_response.category,
            'previous_presentation': previous_response.presentation,
            'previous_actions_accept_checked': 'true' if previous_response.actions_accept else 'false',
            'previous_actions_decline_checked': 'true' if previous_response.actions_decline else 'false',
            'previous_actions_moreinfo_checked': 'true' if previous_response.actions_more_information else 'false',
            'previous_actions_settings_checked': 'true' if previous_response.actions_settings else 'false',
            'previous_actions_close_checked': 'true' if previous_response.actions_close else 'false',
            'previous_actions_privacypolicy_checked': 'true' if previous_response.actions_privacy_policy else 'false',
            'previous_actions_preferencecheckboxes_checked': 'true' if previous_response.actions_preference_checkboxes else 'false',
            'previous_content_trackingcookies_checked': 'true' if previous_response.content_tracking_cookies else 'false',
            'previous_content_othercookies_checked': 'true' if previous_response.content_other_cookies else 'false',
            'previous_content_acceptdefault_checked': 'true' if previous_response.content_default_accept else 'false',
            'previous_content_implieddecline_checked': 'true' if previous_response.content_implied_decline else 'false',
            'previous_content_explicitdecline_checked': 'true' if previous_response.content_explicit_decline else 'false',
            'previous_content_preselectedcheckboxes_checked': 'true' if previous_response.content_preselected_checkboxes else 'false',
            'previous_website_adblockerpresent_checked': 'true' if previous_response.website_adblocker_present else 'false',
            'previous_website_subscriptionoption_checked': 'true' if previous_response.website_subscription_option else 'false',
            'previous_website_paywallpresent_checked': 'true' if previous_response.website_paywall_present else 'false',
            'previous_website_notactive_checked': 'true' if previous_response.website_not_active else 'false',
            'previous_furtherreview_checked': 'true' if previous_response.further_review else 'false',
            'previous_furtherreview_language_checked': 'true' if previous_response.further_review_language else 'false',
            'previous_furtherreview_language_select': previous_response.further_review_language_select,
            'previous_furtherreview_other_checked': 'true' if previous_response.further_review_other else 'false',
            'previous_furtherreview_other_text': previous_response.further_review_other_text,
        }
    except:
        previous_context = {}

    screenshot_context = {
        'domain': screenshot.domain,
        'wave_num': screenshot.wave_id,
        'country': screenshot.country,
        'view_id': screenshot.view_id,
        'channel_id': screenshot.channel_id,
        'imagepath': screenshot.image_path,
        'endpoint': endpoint
    }

    session_context = request.session['session_context']

    # Append Screenshot Info to Task Info
    screenshot_information = '<div><u>Domain:</u> ' + screenshot.domain + '</div>' \
                                                                          '<div><u>Country:</u> ' + screenshot.country + '</div>' \
                                                                                                                         '<div><u>Wave Number:</u> ' + str(
        screenshot.wave_id)
    try:
        session_context['task_information'] = session_context['task_information'] + screenshot_information
    except:
        session_context['task_information'] = screenshot_information

    context = {**existing_context, **previous_context, **screenshot_context, **session_context}

    return render(request, 'screenshot_app/sort.html', context)


def get_task_screenshot(profile, direction, current_screenshot):
    # Get Next Screenshot
    if direction == 'next':

        # Get Screenshots from Assigned Tasks where User Response Object Does Not Exist
        unsorted_screenshots = Screenshot.objects.filter(task__profile__user=profile.user).exclude(
            response__user=profile.user)

        # If Set is Empty, Get New Task
        if len(unsorted_screenshots) == 0:

            # Assign New Task
            if assign_task(profile):
                unsorted_screenshots = Screenshot.objects.filter(task__profile__user=profile.user).exclude(
                    response__user=profile.user)
                new_screenshot = unsorted_screenshots.first()
            else:
                new_screenshot = None
        else:
            # Get First Unsorted Screenshot
            new_screenshot = unsorted_screenshots.first()

    # Get Previous Screenshot
    if direction == 'previous':

        # Get Task that Contains Screenshot
        try:
            current_task = profile.assigned_tasks.filter(screenshots=current_screenshot)
        except Profile.DoesNotExist:
            # Current Screenshot is in Task not Assigned to User
            get_task_screenshot(profile, 'next', current_screenshot)

        for i, screenshot in enumerate(Screenshot.objects.filter(task__in=profile.assigned_tasks.all())):
            if screenshot == current_screenshot:
                try:
                    new_screenshot = Screenshot.objects.filter(task__in=profile.assigned_tasks.all())[i - 1]
                    break
                except:
                    new_screenshot = None
                    break

    # Return Screenshot Object
    return new_screenshot


def assign_task(profile):
    if profile.setting_collaborative_sort:
        # Get Tasks that No Users have Completed
        unfinished_tasks = Task.objects.filter(profile__user=None)
    else:
        # Get Tasks that Current User has Not Completed
        unfinished_tasks = Task.objects.exclude(profile__user=profile.user)

    # Assign First Task in Queue to User
    new_task = unfinished_tasks.order_by('id').first()
    if new_task is not None:
        profile.assigned_tasks.add(new_task)
        profile.save()
        return True
    else:
        return False


def save_response(request, current_screenshot, target_user):
    # Get Form Data
    category = request.POST.get('category')
    presentation = request.POST.get('presentation')
    actions = request.POST.getlist('actions')
    content = request.POST.getlist('content')
    website = request.POST.getlist('website')
    further_review_language_select = request.POST.get('furtherreview_language_select')
    further_review_other_text = request.POST.get('furtherreview_other_text')

    # Create or Update Response from Form Data
    try:
        response = Response.objects.get(screenshot=current_screenshot, user=target_user)
    except Response.DoesNotExist:
        response = Response()

    response.screenshot = current_screenshot
    response.user = target_user
    response.category = category
    response.presentation = presentation
    response.actions_accept = True if 'accept' in actions else False
    response.actions_decline = True if 'decline' in actions else False
    response.actions_more_information = True if 'moreinfo' in actions else False
    response.actions_settings = True if 'settings' in actions else False
    response.actions_close = True if 'close' in actions else False
    response.actions_privacy_policy = True if 'privacypolicy' in actions else False
    response.actions_preference_checkboxes = True if 'preferencecheckboxes' in actions else False
    response.content_tracking_cookies = True if 'trackingcookies' in content else False
    response.content_other_cookies = True if 'othercookies' in content else False
    response.content_default_accept = True if 'acceptdefault' in content else False
    response.content_implied_decline = True if 'implieddecline' in content else False
    response.content_explicit_decline = True if 'explicitdecline' in content else False
    response.content_preselected_checkboxes = True if 'preselectedcheckboxes' in content else False
    response.website_adblocker_present = True if 'adblockerpresent' in website else False
    response.website_subscription_option = True if 'subscriptionoption' in website else False
    response.website_paywall_present = True if 'paywallpresent' in website else False
    response.website_not_active = True if 'notactive' in website else False
    response.further_review = True if request.POST.get('furtherreview') else False
    response.further_review_language = True if request.POST.get('furtherreview_language') else False
    response.further_review_language_select = further_review_language_select
    response.further_review_other = True if request.POST.get('furtherreview_other') else False
    response.further_review_other_text = further_review_other_text

    # Save Response to Database
    response.save()

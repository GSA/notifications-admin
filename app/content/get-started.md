<h1 class="font-body-2xl margin-bottom-3">Get started</h1>

<ol class="usa-process-list">
  <li class="usa-process-list__item padding-bottom-4 margin-top-2">
    <h2 class="usa-process-list__heading line-height-sans-3">Check if Notify.gov is right for you</h2>
    <p>Read about our <a class="usa-link" href="{{ url_for('main.features') }}">features</a>, <a class="usa-link" href="{{ url_for('.pricing') }}">pricing</a> and <a class="usa-link" href="{{ url_for('main.roadmap') }}">roadmap</a>.</p>
  </li>

  <li class="usa-process-list__item padding-bottom-4">
    <h2 class="usa-process-list__heading line-height-sans-3">Create an account</h2>
    {% if not current_user.is_authenticated %}
      <p><a class="usa-link" href="{{ url_for('.register') }}">Create an account</a> for free and add your first Notify service. When you add a new service it will start in <a class="usa-link" href="{{ url_for('main.trial_mode_new') }}">trial mode</a>.</p>
    {% else %}
      <p>Create an account for free and add your first Notify service. When you add a new service, it will start in <a class="usa-link" href="{{ url_for('main.trial_mode_new') }}">trial mode</a>.</p>
    {% endif %}
  </li>

  <li class="usa-process-list__item padding-bottom-4">
    <h2 class="usa-process-list__heading line-height-sans-3">Write some messages</h2>
    <p>Add message templates with examples of the content you plan to send. You can use our <a class="usa-link" href="{{ url_for('main.guidance_index') }}">guidance</a> to help you.</p>
  </li>

  <li class="usa-process-list__item padding-bottom-4">
    <h2 class="usa-process-list__heading line-height-sans-3">Set up your service</h2>
    {% if not current_user.is_authenticated or not current_service %}
    <p>Review your settings to add message branding and sender information.</p>
    <p>Add team members and check their permissions.</p>
    {% else %}
    <p>Review your <a class="usa-link" href="{{ url_for('.service_settings', service_id=current_service.id) }}">settings</a> to add message branding and sender information.</p>
    <p>Add <a class="usa-link" href="{{ url_for('.manage_users', service_id=current_service.id) }}">team members</a> and check their permissions.</p>
    {% endif %}
  </li>

  <!-- <li class="get-started-list__item">
    <h2 class="usa-process-list__heading  line-height-sans-1">Set up an API integration (optional)</h2>
    <p>You can use the Notify API to send messages automatically.</p>
    <p>Our <a class="usa-link" href="{{ url_for('main.documentation') }}">documentation</a> explains how to integrate the API with a web application or back office system.</p>
  </li> -->

  <li class="usa-process-list__item padding-bottom-4">
    <h2 class="usa-process-list__heading line-height-sans-3">Start sending messages</h2>
    {% if not current_user.is_authenticated or not current_service %}
    <p>When you’re ready to send messages to people outside your team, go to the <b class="bold">Settings</b> page and select <b class="bold">Request to go live</b>. We’ll approve your request within one working day.</p>
    {% else %}
    <p>You should <a class="usa-link" href="{{ url_for('.request_to_go_live', service_id=current_service.id) }}">request to go live</a> when you’re ready to send messages to people outside your team. We’ll approve your request within one working day.</p>
    {% endif %}
    <!-- <p>Check <a class="usa-link" href="{{ url_for('main.how_to_pay') }}">how to pay</a> if you’re planning to exceed the <a class="usa-link" href="{{ url_for('.pricing', _anchor='text-messages') }}">free text message allowance</a>.</p> -->
  </li>

</ol>
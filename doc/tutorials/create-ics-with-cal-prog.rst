Create a ICS File with Thunderbird
==================================

.. meta::
   :keywords: Thunderbird
   :keywords: export calendar

.. topic:: Abstract

   In this document, we introduce Thunderbird. Although it's a classical e-mail
   program, but we use it solely as a calendar.
   This tutorial shows how to create a calendar, add some entires, and
   to export its calendar content to a ``.ics`` file. This can be helpful,
   if you want to either test, access certain functions, or play with ics.py.

.. contents::  Content
   :local:


.. _sec.tb.installing:

Installing Thunderbird
----------------------

Thunderbird is available for Linux, MacOS, and Windows.


Installing on Linux
~~~~~~~~~~~~~~~~~~~

For most cases, Thunderbird is already packaged for your Linux distribution.
This means, you can use the package manager of your system. It could be
that your system has an older version, but for this tutorial, this does not
matter. To install Thunderbird on your system, you need to become root,
the system administrator.

Use the following commands:

* Debian/Ubuntu::

  $ sudo apt-get update
  $ sudo apt-get install thunderbird

* Fedora::

  $ dnf install thunderbird

* openSUSE::

  $ sudo zypper install thunderbird


Installing on MacOS
~~~~~~~~~~~~~~~~~~~

Follow the article on https://support.mozilla.org/en-US/kb/installing-thunderbird-on-mac



Installing on Windows
~~~~~~~~~~~~~~~~~~~~~

Follow the article on https://support.mozilla.org/en-US/kb/installing-thunderbird-windows


.. _sec.tb.create-calendar:

Creating a Calendar in Thunderbird
----------------------------------

First we need a calendar to attach all entries to it. Proceed as follows:

#. Start Thunderbird.
#. From the menu, choose :menuselection:`File --> New --> Calendar`.
   If the menu is hidden, hit the :kbd:`F10` key.
#. Leave the option :guilabel:`On My Computer` (default) unchanged. Click :guilabel:`Next`.
#. Set a name for your calendar and an optional color. You can leave the
   Email to :guilabel:`None`.
#. Click :guilabel:`Next` and then :guilabel:`Finish`.


.. _sec.tb.add-entries:

Adding Events to Your Calendar
------------------------------

#. From the menu, choose :menuselection:`File --> New --> Event...`
#. Enter a title.
#. Make sure that the :guilabel:`Calendar:` field contains the name of your
   calendar that you have created in section :ref:`sec.tb.create-calendar`.
   This is important as if you choose the wrong calendar, your entry will
   end up in a completely different location (and is not available in the
   expected file).
#. Set the start and (optionally) the end date. If needed, add a time or
   check All day Event.
#. Optionally, you can set a recurring date, a reminder and a description.
#. When finished, click Save and Close.
#. Repeat the above steps as needed.


.. _sec.tb.export:

Exporting All Entries from a Calendar
-------------------------------------

After you have added one or more entires to your calender, export it to
a ics file:

#. From the menu, choose :menuselection:`Events and Tasks --> Export...`
#. In the dialog box, choose the calendar you want to export and proceed
   with Ok.
#. Choose the file location of the ics file. Make sure you use
   :guilabel:`iCalendar (*.ics)` as filter. Click :guilabel:`Save` to finish.

Your calendar is exported as ics file and can be used.

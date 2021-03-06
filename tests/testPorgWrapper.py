#!/usr/bin/env python3.5
import sqlite3
import unittest
from datetime import datetime, timedelta

from config import porg_config
from gen_db import generate as generate_db
from Poorganiser import User, Event, Attendance, Question, Survey, Choice, Response
from PorgWrapper import PorgWrapper
from PorgExceptions import *


class TestPorgWrapper(unittest.TestCase):
    def setUp(self):
        generate_db(c)  # Generate blank database

    def tearDown(self):
        # generate_db(c)  # Generate blank database
        pass

    def test_get_user_by_username(self):
        self.assertIsNone(p.get_user_by_username("bob"))
        self.assertIsNone(p.get_user_by_username("jane"))

    def test_register_user(self):
        # Check that no users currently exist with usernames "bob"/"dave and friends"
        self.assertIsNone(p.get_user_by_username("bob"))
        self.assertIsNone(p.get_user_by_username("dave and friends"))

        u = p.register_user("bob")
        self.assertEqual(u.get_username(), "bob")
        self.assertEqual(u.get_events_organised_ids(), [])
        self.assertEqual(u.get_events_attending_ids(), [])

        u = p.register_user("dave and friends")
        self.assertEqual(u.get_username(), "dave and friends")
        self.assertEqual(u.get_events_organised_ids(), [])
        self.assertEqual(u.get_events_attending_ids(), [])

        # Test querying created users from database
        u2 = p.get_user_by_username("bob")
        self.assertTrue(isinstance(u2, User))
        self.assertEqual(u2.get_username(), "bob")
        self.assertEqual(u2.get_events_organised_ids(), [])
        self.assertEqual(u2.get_events_attending_ids(), [])

        u2 = p.get_user_by_username("dave and friends")
        self.assertTrue(isinstance(u2, User))
        self.assertEqual(u2.get_username(), "dave and friends")
        self.assertEqual(u2.get_events_organised_ids(), [])
        self.assertEqual(u2.get_events_attending_ids(), [])

        # Check that re-registering same username raises UserRegisteredError
        with self.assertRaises(UserRegisteredError):
            p.register_user("bob")

        with self.assertRaises(UserRegisteredError):
            p.register_user("dave and friends")

    def test_unregister_user(self):
        # Register some users
        u1 = p.register_user("bob")
        u2 = p.register_user("jane")
        u3 = p.register_user("noot noot")

        # Create some events
        e1 = p.create_event("event 1", u1)
        e2 = p.create_event("event 2", u2.get_id())
        e3 = p.create_event("event3", u2, location="blob street")
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id()])
        self.assertEqual(u2.get_events_organised_ids(), [e2.get_id(), e3.get_id()])

        # Create some surveys
        s1 = p.create_survey("survey 1", u1, event_obj=e1)
        s2 = p.create_survey("survey 2", u2, event_obj=e2)
        s3 = p.create_survey("survey 3", u2, event_obj=e1)

        # Create some questions
        q1 = p.create_question(u1, "lol", "free")
        q2 = p.create_question(u1, "something", "free", survey_obj=s1)

        # Unregister created users
        p.unregister_user(u1)  # Only delete attendances - event should still exist
        self.assertIsNone(e1.get_owner_id())  # Check owner_id is removed from Event
        self.assertIsNotNone(p.db_interface.get_obj(e1.get_id(), Event))
        self.assertIsNone(p.get_attendance(u1.get_id(), e1.get_id()))  # Check attendance deleted
        self.assertIsNone(p.db_interface.get_obj(s1.get_id(), Survey))  # Check survey deleted

        # Check non-associated question deleted
        self.assertIsNone(p.db_interface.get_obj(q1.get_id(), Question))

        # Check survey-associated question deleted
        self.assertIsNone(p.db_interface.get_obj(q2.get_id(), Question))

        p.unregister_user("jane", delete_events=True)  # Delete attendances and events
        self.assertIsNone(p.db_interface.get_obj(e2.get_id(), Event))
        self.assertIsNone(p.db_interface.get_obj(e2.get_id(), Event))
        self.assertIsNone(p.get_attendance(u2.get_id(), e2.get_id()))  # Check attendance deleted
        self.assertIsNone(p.get_attendance(u2.get_id(), e3.get_id()))  # Check attendance deleted

        # Check surveys deleted
        self.assertIsNone(p.db_interface.get_obj(s2.get_id(), Survey))
        self.assertIsNone(p.db_interface.get_obj(s3.get_id(), Survey))

        p.unregister_user(u3)

        # Try unregister users that have already been unregistered
        with self.assertRaises(UserNotFoundError):
            p.unregister_user("bob")

        with self.assertRaises(UserNotFoundError):
            p.unregister_user(u2)

        with self.assertRaises(UserNotFoundError):
            p.unregister_user("noot noot")

        # Try unregister users that don't exist
        with self.assertRaises(UserNotFoundError):
            p.unregister_user("blargh")

        with self.assertRaises(UserNotFoundError):
            p.unregister_user("1234")

        with self.assertRaises(UserNotFoundError):
            p.unregister_user(1234)

    def test_get_curr_events(self):
        # Sanity check - no events initially
        curr_events = p.get_curr_events()
        self.assertEqual(curr_events, [])

        # Create some users
        u1 = p.register_user("bob")
        u2 = p.register_user("josh")

        # Sanity checks - u1 and u2 have correct ids
        self.assertEqual(u1.get_id(), 1)
        self.assertEqual(u2.get_id(), 2)

        # Create some events
        e1 = p.create_event("event 1", 1)
        e2 = p.create_event("event 2", 2, location="location 2")
        e3 = p.create_event("event 3", 2, time=datetime.today() + timedelta(days=10))

        # Check current events are as expected
        curr_events = p.get_curr_events()
        self.assertEqual(curr_events, [e1, e2, e3])

        # Create events dated before today, check they don't appear in curr_events
        before_yesterday = datetime.today() - timedelta(days=134)
        yesterday = datetime.today() - timedelta(days=1)
        p.create_event("event 4", 1, time=yesterday, location="location 4")
        p.create_event("event 5", 1, time=before_yesterday)
        curr_events = p.get_curr_events()
        self.assertEqual(curr_events, [e1, e2, e3])

    def test_get_events_by_user(self):
        # Create some users
        u1 = p.register_user("jane")
        u2 = p.register_user("user 2")

        # Sanity checks - u1 and u2 have correct ids
        self.assertEqual(u1.get_id(), 1)
        self.assertEqual(u2.get_id(), 2)

        # Check that u1 and u2 don't have events
        u1_events = p.get_events_by_user(u1)
        u2_events = p.get_events_by_user(u2.get_id())
        self.assertEqual(u1_events, [])
        self.assertEqual(u2_events, [])

        # Create some events for u1
        e1 = p.create_event("event 1a", u1.get_id())
        u1_events = p.get_events_by_user(u1)
        self.assertEqual(u1_events, [e1])

        e2 = p.create_event("event 2a", u1)
        u1_events = p.get_events_by_user(u1.get_id())
        self.assertEqual(u1_events, [e1, e2])

        # Create some events for u2, check none of u1's events were added to u2
        u2_events = p.get_events_by_user(u2)
        self.assertEqual(u2_events, [])
        e3 = p.create_event("event 1b", u2)
        u2_events = p.get_events_by_user(u2)
        self.assertEqual(u2_events, [e3])

        e4 = p.create_event("event 2b", u2.get_id())
        u2_events = p.get_events_by_user(u2)
        self.assertEqual(u2_events, [e3, e4])

        # Check event deletions
        p.delete_event(e4)
        u2_events = p.get_events_by_user(u2)
        self.assertEqual(u2_events, [e3])

        p.delete_event(e3)
        u2_events = p.get_events_by_user(u2)
        self.assertEqual(u2_events, [])

    def test_get_all_events(self):
        # Check there are no events at the beginning
        events = p.get_all_events()
        self.assertEqual(events, [])

        # Create some users
        u1 = p.register_user("user 1")

        # Add some events
        e1 = p.create_event("event 1", u1.get_id())

        all_events = p.get_all_events()
        self.assertEqual(all_events, [e1])

        e2 = p.create_event("event 2", u1.get_id(), location="loc1")
        all_events = p.get_all_events()
        self.assertEqual(all_events, [e1, e2])

        yesterday = datetime.today() - timedelta(days=1)
        e3 = p.create_event("event 3", u1.get_id(), time=yesterday)
        all_events = p.get_all_events()
        self.assertEqual(all_events, [e1, e2, e3])

    def test_create_event(self):
        # Create some users
        u1 = p.register_user("user_1")
        u2 = p.register_user("the second UsEr")

        # Sanity checks
        self.assertEqual(u1.get_id(), 1)
        self.assertEqual(u2.get_id(), 2)

        # Create some events
        # No specified location/time
        e1 = p.create_event("event 1", u1.get_id())
        a1 = p.get_attendance(u1.get_id(), e1.get_id())
        self.assertEqual(e1.get_id(), 1)
        self.assertEqual(e1.get_name(), "event 1")
        self.assertIsNone(e1.get_location())
        self.assertIsNone(e1.get_time())
        self.assertEqual(p.get_attendances(e1), [a1])

        # Check events_organised_ids and events_attending_ids for u1
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id()])

        # Check auto-created attendance for e1
        self.assertEqual(a1.get_user_id(), u1.get_id())
        self.assertEqual(a1.get_event_id(), e1.get_id())
        self.assertEqual(a1.get_going_status(), "going")
        self.assertEqual(a1.get_roles(), ["organiser"])

        # Specified location, no specified time
        e2 = p.create_event("event 2", u1.get_id(), location="somewhere over there")
        a2 = p.get_attendance(u1.get_id(), e2.get_id())
        self.assertEqual(e2.get_name(), "event 2")
        self.assertEqual(e2.get_location(), "somewhere over there")
        self.assertIsNone(e2.get_time())
        self.assertEqual(p.get_attendances(e2), [a2])

        # Check events_organised_ids and events_attending_ids for u1
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id(), e2.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id(), e2.get_id()])

        # Check auto-created attendance for e2
        self.assertEqual(a2.get_user_id(), u1.get_id())
        self.assertEqual(a2.get_event_id(), e2.get_id())
        self.assertEqual(a2.get_going_status(), "going")
        self.assertEqual(a2.get_roles(), ["organiser"])

        # Specified time, no specified location
        third_time = datetime(year=2016, month=4, day=1)
        e3 = p.create_event("events are cool", u1.get_id(), time=third_time)
        a3 = p.get_attendance(u1.get_id(), e3.get_id())
        self.assertEqual(e3.get_name(), "events are cool")
        self.assertIsNone(e3.get_location())
        self.assertEqual(e3.get_time(), third_time)
        self.assertEqual(p.get_attendances(e3), [a3])

        # Check events_organised_ids and events_attending_ids for u1
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id(), e2.get_id(), e3.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id(), e2.get_id(), e3.get_id()])

        # Check auto-created attendance for e3
        self.assertEqual(a3.get_user_id(), u1.get_id())
        self.assertEqual(a3.get_event_id(), e3.get_id())
        self.assertEqual(a3.get_going_status(), "going")
        self.assertEqual(a3.get_roles(), ["organiser"])

        # Specified location and time
        fourth_time = datetime(year=2017, month=10, day=25)
        e4 = p.create_event("THE (4th) EVENT", u2.get_id(), location="not here", time=fourth_time)
        a4 = p.get_attendance(u2.get_id(), e4.get_id())
        self.assertEqual(e4.get_name(), "THE (4th) EVENT")
        self.assertEqual(e4.get_location(), "not here")
        self.assertEqual(e4.get_time(), fourth_time)
        self.assertEqual(p.get_attendances(e4), [a4])

        # Check events_organised_ids and events_attending_ids for u1 and u2
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id(), e2.get_id(), e3.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id(), e2.get_id(), e3.get_id()])
        self.assertEqual(u2.get_events_organised_ids(), [e4.get_id()])
        self.assertEqual(u2.get_events_attending_ids(), [e4.get_id()])

        # Check auto-created attendance for e4
        self.assertEqual(a4.get_user_id(), u2.get_id())
        self.assertEqual(a4.get_event_id(), e4.get_id())
        self.assertEqual(a4.get_going_status(), "going")
        self.assertEqual(a4.get_roles(), ["organiser"])

        # Test creating events with user ids that don't exist
        with self.assertRaises(UserNotFoundError):
            p.create_event("fourth invalid event", 0)
        with self.assertRaises(UserNotFoundError):
            p.create_event("something", 1023, location="blah")
        with self.assertRaises(UserNotFoundError):
            p.create_event("lalalalal", -321, location="alalala", time=fourth_time)

        # Check correct all_events
        all_events = p.get_all_events()
        self.assertEqual(all_events, [e1, e2, e3, e4])

        # Check u1 and u2 still have correct events_organised_ids and events_attending_ids
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id(), e2.get_id(), e3.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id(), e2.get_id(), e3.get_id()])
        self.assertEqual(u2.get_events_organised_ids(), [e4.get_id()])
        self.assertEqual(u2.get_events_attending_ids(), [e4.get_id()])

    def test_delete_event(self):
        # Create some users
        u1 = p.register_user("user1")
        u2 = p.register_user("ThE sEcOnD uSeR")

        # Create some events
        e1 = p.create_event("event 1", u1.get_id())
        e2 = p.create_event("two to 2 too", u2.get_id())
        e3 = p.create_event("free threes", u1.get_id())

        # Create some surveys
        s1 = p.create_survey("survey 1", u1, event_obj=e1)
        s2 = p.create_survey("survey 2", u1, event_obj=e1)
        s3 = p.create_survey("survey 2", u1)

        a1 = p.get_attendance(u1.get_id(), e1.get_id())
        a2 = p.get_attendance(u2.get_id(), e2.get_id())
        a3 = p.get_attendance(u1.get_id(), e3.get_id())

        # Check events_organising_ids and events_attending_ids for u1 and u2
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id(), e3.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id(), e3.get_id()])
        self.assertEqual(u2.get_events_organised_ids(), [e2.get_id()])
        self.assertEqual(u2.get_events_attending_ids(), [e2.get_id()])

        # Check attendances for created events
        self.assertEqual(p.get_attendances(e1), [a1])
        self.assertEqual(p.get_attendances(e2), [a2])
        self.assertEqual(p.get_attendances(e3), [a3])

        # Check surveys created
        self.assertIsNotNone(p.db_interface.get_obj(s1.get_id(), Survey))
        self.assertIsNotNone(p.db_interface.get_obj(s2.get_id(), Survey))
        self.assertIsNotNone(p.db_interface.get_obj(s3.get_id(), Survey))

        # Delete e1
        p.delete_event(e1)

        # Check user's events_organised_ids and events_attending_ids were removed
        self.assertEqual(u1.get_events_organised_ids(), [e3.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e3.get_id()])

        # Check attendances were removed
        self.assertIsNone(p.get_attendance(u1.get_id(), e1.get_id()))

        # Check surveys were deleted
        self.assertIsNone(p.db_interface.get_obj(s1.get_id(), Survey))
        self.assertIsNone(p.db_interface.get_obj(s2.get_id(), Survey))
        self.assertIsNotNone(p.db_interface.get_obj(s3.get_id(), Survey))  # Should remain - not associated with d3

        # Delete e2 by id
        p.delete_event(e2.get_id())

        # Check user's events_organised_ids and events_attending_ids were removed
        self.assertEqual(u2.get_events_organised_ids(), [])
        self.assertEqual(u2.get_events_attending_ids(), [])

        # Check attendances were removed
        self.assertIsNone(p.get_attendance(u2.get_id(), e2.get_id()))

        # Delete e3
        p.delete_event(e3)

        # Check user's events_organised_ids and events_attending_ids were removed
        self.assertEqual(u1.get_events_organised_ids(), [])
        self.assertEqual(u1.get_events_attending_ids(), [])

        # Check attendances were removed
        self.assertIsNone(p.get_attendance(u1.get_id(), e3.get_id()))

        # Try delete events that don't exist in database
        with self.assertRaises(EventNotFoundError):
            p.delete_event(e1)

        with self.assertRaises(EventNotFoundError):
            p.delete_event(e3)

        with self.assertRaises(EventNotFoundError):
            p.delete_event(103)

        with self.assertRaises(EventNotFoundError):
            p.delete_event(Event("some event", u1.get_id()))

        # Try delete events with owners that no longer exist in database
        e4 = p.create_event("event_to_be_deleted", u1.get_id())
        p.unregister_user(u1)
        p.delete_event(e4)

        # Check no more events returned by get_curr_events and get_all_events
        self.assertEqual(p.get_curr_events(), [])
        self.assertEqual(p.get_all_events(), [])

    def test_get_attendance(self):
        # Create some users
        u1 = p.register_user("u1")
        u2 = p.register_user("u2")
        u3 = p.register_user("u3")

        # Create some events
        e1 = p.create_event("e1", u1)
        a1 = p.get_attendance(u1.get_id(), e1.get_id())

        # Check fields for auto-created Attendance for e1
        self.assertEqual(a1.get_user_id(), u1.get_id())
        self.assertEqual(a1.get_event_id(), e1.get_id())
        self.assertEqual(a1.get_going_status(), "going")
        self.assertEqual(a1.get_roles(), ['organiser'])

        # Create attendance
        a2 = p.create_attendance(u2, e1)
        a2_gotten = p.get_attendance(u2, e1)
        self.assertEqual(a2_gotten.get_user_id(), u2.get_id())
        self.assertEqual(a2_gotten.get_event_id(), e1.get_id())
        self.assertEqual(a2.get_going_status(), "invited")
        self.assertEqual(a2.get_roles(), [])
        self.assertEqual(a2, a2_gotten)

        e2 = p.create_event("e2", u3)
        a2 = p.get_attendance(u3, e2)

        # Check fields for auto-created Attendance for e2
        self.assertEqual(a2.get_user_id(), u3.get_id())
        self.assertEqual(a2.get_event_id(), e2.get_id())
        self.assertEqual(a2.get_going_status(), "going")
        self.assertEqual(a2.get_roles(), ['organiser'])

        # Create attendance
        a3 = p.create_attendance(u2, e2, going_status="maybe")
        a3_gotten = p.get_attendance(u2, e2)
        self.assertEqual(a3.get_user_id(), u2.get_id())
        self.assertEqual(a3.get_event_id(), e2.get_id())
        self.assertEqual(a3.get_going_status(), "maybe")
        self.assertEqual(a3.get_roles(), [])
        self.assertEqual(a3, a3_gotten)

        a4 = p.create_attendance(u1, e2, going_status="invited", roles=["food buyer", "driver"])
        a4_gotten = p.get_attendance(u1, e2)
        self.assertEqual(a4.get_user_id(), u1.get_id())
        self.assertEqual(a4.get_event_id(), e2.get_id())
        self.assertEqual(a4.get_going_status(), "invited")
        self.assertEqual(a4.get_roles(), ['food buyer', 'driver'])
        self.assertEqual(a4, a4_gotten)

        # Try get attendances that don't exist
        self.assertIsNone(p.get_attendance(100, 200))
        self.assertIsNone(p.get_attendance(u1, "asdf"))
        self.assertIsNone(p.get_attendance(3, e1))

    def test_get_attendances(self):
        # Create some users
        u1 = p.register_user("u1")
        u2 = p.register_user("u2")
        u3 = p.register_user("u3")

        # Create some events
        e1 = p.create_event("e1", u1)
        a1 = p.get_attendance(u1, e1)
        self.assertEqual(p.get_attendances(e1), [a1])  # Test on Event
        self.assertEqual(p.get_attendances(e1), p.get_attendances(u1))  # Test on User

        a2 = p.create_attendance(u2, e1)
        self.assertEqual(p.get_attendances(e1), [a1, a2])
        self.assertEqual(p.get_attendances(u2), [a2])

        e2 = p.create_event("e2", u2, location="springfield")
        a3 = p.get_attendance(u2, e2)
        self.assertEqual(p.get_attendances(e2), [a3])
        self.assertEqual(p.get_attendances(u2), [a2, a3])

        a4 = p.create_attendance(u3, e2)
        self.assertEqual(p.get_attendances(e2), [a3, a4])
        self.assertEqual(p.get_attendances(u3), [a4])

        a5 = p.create_attendance(u1, e2)
        self.assertEqual(p.get_attendances(e2), [a3, a4, a5])
        self.assertEqual(p.get_attendances(u1), [a1, a5])

        # Try call get_attendance with invalid parameter types
        with self.assertRaises(TypeError):
            p.get_attendances(a1)

        with self.assertRaises(TypeError):
            p.get_attendances(12345)

        with self.assertRaises(TypeError):
            p.get_attendances("event 1")

    def test_create_attendance(self):
        # Create some users
        u1 = p.register_user("u1")
        u2 = p.register_user("u2")
        u3 = p.register_user("u3")

        e1 = p.create_event("e1", u1)
        a1 = p.get_attendance(u1, e1)
        a2 = p.create_attendance(u2, e1)

        # Check properties of created Attendance
        self.assertEqual(a2.get_user_id(), u2.get_id())
        self.assertEqual(a2.get_event_id(), e1.get_id())
        self.assertEqual(a2.get_going_status(), "invited")
        self.assertEqual(a2.get_roles(), [])

        # Check events_attending_ids for User was updated
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id()])
        self.assertEqual(u2.get_events_attending_ids(), [e1.get_id()])

        # Check attendance_ids for Event was updated
        self.assertEqual(e1.get_attendance_ids(), [a1.get_id(), a2.get_id()])

        a3 = p.create_attendance(u3, e1, going_status="idk lol", roles=["hat wearer", "cook"])

        # Check properties of created Attendance
        self.assertEqual(a3.get_user_id(), u3.get_id())
        self.assertEqual(a3.get_event_id(), e1.get_id())
        self.assertEqual(a3.get_going_status(), "idk lol")
        self.assertEqual(a3.get_roles(), ["hat wearer", "cook"])

        # Check events_attending_ids for users was updated
        self.assertEqual(u3.get_events_attending_ids(), [e1.get_id()])

        # Check attendance_ids for Event was updated
        self.assertEqual(e1.get_attendance_ids(), [a1.get_id(), a2.get_id(), a3.get_id()])

        # Test creating duplicate events (event a user is already attending)
        with self.assertRaises(DuplicateAttendanceError):
            p.create_attendance(u1, e1)

        with self.assertRaises(DuplicateAttendanceError):
            p.create_attendance(u3, e1)

        # Test attendance creation with events that don't exist
        with self.assertRaises(EventNotFoundError):
            p.create_attendance(u1, Event("nonexistant event", u1.get_id()))

        with self.assertRaises(EventNotFoundError):
            p.create_attendance(u1, Event("nonexistant event 2", u2.get_id(), location="blah"))

        # Test attendance creation with users that don't exist
        with self.assertRaises(UserNotFoundError):
            p.create_attendance(User("nonexistant user"), e1)

        with self.assertRaises(UserNotFoundError):
            p.create_attendance(User("nonexistant user 2"), e1)

    def test_delete_attendance(self):
        # Create some users
        u1 = p.register_user("u1")
        u2 = p.register_user("u2")

        e1 = p.create_event("e1", u1)
        a1 = p.get_attendance(u1, e1)

        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id()])
        self.assertEqual(u1.get_events_attending_ids(), [e1.get_id()])
        self.assertEqual(e1.get_attendance_ids(), [a1.get_id()])

        p.delete_attendance(a1)

        # Check event id removed from events_attending_ids but not events_organised_ids
        self.assertEqual(u1.get_events_organised_ids(), [e1.get_id()])  # Still organising event...
        self.assertEqual(u1.get_events_attending_ids(), [])  # ... but not attending

        # Check attendance id removed from Event
        self.assertEqual(e1.get_attendance_ids(), [])

        # Create second Attendance
        a2 = p.create_attendance(u2, e1)

        # Check attendance id removed from Event
        self.assertEqual(e1.get_attendance_ids(), [a2.get_id()])

        # u2 did not organise e1
        self.assertEqual(u2.get_events_organised_ids(), [])
        self.assertEqual(u2.get_events_attending_ids(), [e1.get_id()])
        self.assertEqual(e1.get_attendance_ids(), [a2.get_id()])

        p.delete_attendance(a2)

        # Check event id removed from events_attending_ids, events_organised_ids still empty
        self.assertEqual(u2.get_events_organised_ids(), [])
        self.assertEqual(u2.get_events_attending_ids(), [])

        # Check attendance id removed from Event
        self.assertEqual(e1.get_attendance_ids(), [])

        # Try delete attendances that don't exist
        with self.assertRaises(AttendanceNotFoundError):
            p.delete_attendance(Attendance(1, 1))

        with self.assertRaises(AttendanceNotFoundError):
            p.delete_attendance(Attendance(1, e1.get_id()))

        with self.assertRaises(AttendanceNotFoundError):
            p.delete_attendance(Attendance(u1.get_id(), e1.get_id()))

    def test_create_choice(self):
        u1 = p.register_user("user1")
        q = p.create_question(u1, "Hello?", "free")
        self.assertEqual(q.get_allowed_choice_ids(), [])
        ch = p.create_choice(q, "choice 1")
        self.assertEqual(ch.get_id(), 1)
        self.assertEqual(ch.get_question_id(), q.get_id())
        self.assertEqual(ch.get_choice(), "choice 1")
        self.assertEqual(q.get_allowed_choice_ids(), [ch.get_id()])

        ch2 = p.create_choice(q, "choice 2")
        self.assertEqual(ch2.get_id(), 2)
        self.assertEqual(ch2.get_question_id(), q.get_id())
        self.assertEqual(ch2.get_choice(), "choice 2")
        self.assertEqual(q.get_allowed_choice_ids(), [ch.get_id(), ch2.get_id()])

        q = p.create_question(u1.get_id(), "write something", "free")
        ch = p.create_choice(q, "choice 1.3")
        self.assertEqual(ch.get_id(), 3)
        self.assertEqual(ch.get_question_id(), q.get_id())
        self.assertEqual(ch.get_choice(), "choice 1.3")
        self.assertEqual(q.get_allowed_choice_ids(), [ch.get_id()])

        # Test creation with questions that don't exist
        with self.assertRaises(QuestionNotFoundError):
            p.create_choice(Question(42, "LOL", "free"), "choice")

        with self.assertRaises(QuestionNotFoundError):
            p.create_choice(Question(3, "blah", "free"), "choice 2")

    def test_create_question(self):
        u1 = p.register_user("user1")
        q = p.create_question(u1.get_id(), "Hello?", "free")
        self.assertEqual(q.get_id(), 1)
        self.assertEqual(q.get_owner_id(), 1)
        self.assertEqual(q.get_question(), "Hello?")
        self.assertEqual(q.get_question_type(), "free")
        self.assertEqual(q.get_survey_id(), None)
        self.assertEqual(q.get_allowed_choice_ids(), [])

        # Check User.question_ids was updated
        self.assertEqual(u1.get_question_ids(), [q.get_id()])

        u2 = p.register_user("User 1")
        s = p.create_survey("SOME COOL SURVEY", u2)
        self.assertEqual(s.get_question_ids(), [])
        q1 = p.create_question(u2.get_id(), "question 1", "free", survey_obj=s)
        self.assertEqual(q1.get_id(), 2)
        self.assertEqual(q1.get_owner_id(), 2)
        self.assertEqual(q1.get_question(), "question 1")
        self.assertEqual(q1.get_question_type(), "free")
        self.assertEqual(q1.get_survey_id(), s.get_id())
        self.assertEqual(q1.get_allowed_choice_ids(), [])

        # Check User.question_ids was updated
        self.assertEqual(u2.get_question_ids(), [q1.get_id()])

        # Check Survey.question_ids was updated
        self.assertEqual(s.get_question_ids(), [q1.get_id()])

        q2 = p.create_question(u1, "the sec0nd question", "free", survey_obj=s)
        self.assertEqual(q2.get_id(), 3)
        self.assertEqual(q2.get_owner_id(), 1)
        self.assertEqual(q2.get_question(), "the sec0nd question")
        self.assertEqual(q2.get_question_type(), "free")
        self.assertEqual(q2.get_survey_id(), s.get_id())
        self.assertEqual(q2.get_allowed_choice_ids(), [])

        # Check User.question_ids was updated
        self.assertEqual(u1.get_question_ids(), [q.get_id(), q2.get_id()])

        # Check Survey.question_ids was updated
        self.assertEqual(s.get_question_ids(), [q1.get_id(), q2.get_id()])

        # Test creation with invalid question types
        with self.assertRaises(InvalidQuestionTypeError):
            p.create_question(89, "invalid question", "invalid")

        with self.assertRaises(InvalidQuestionTypeError):
            p.create_question(12, "invalid question", 3)

        with self.assertRaises(InvalidQuestionTypeError):
            p.create_question(42, "invalid question", ["free"])

        # Test creation with surveys that don't exist
        with self.assertRaises(SurveyNotFoundError):
            p.create_question(u1.get_id(), "q1", "free", Survey("s1", 3))

        with self.assertRaises(SurveyNotFoundError):
            p.create_question(u1.get_id(), "q2", "free", Survey("s2", 183))

    def test_create_response(self):
        u1 = p.register_user("USER 1")
        q1 = p.create_question(u1, "QUESTION?", "free")
        r1 = p.create_response(u1, q1)

        self.assertEqual(r1.get_id(), 1)
        self.assertEqual(r1.get_responder_id(), u1.get_id())
        self.assertEqual(r1.get_question_id(), q1.get_id())
        self.assertEqual(r1.get_response_text(), None)
        self.assertEqual(r1.get_choice_ids(), [])

        # Check response_id was added to User.response_ids
        self.assertEqual(u1.get_response_ids(), [r1.get_id()])

        # Check response_id was added to Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r1.get_id()])

        r2 = p.create_response(u1, q1, response_text="lololol")
        self.assertEqual(r2.get_id(), 2)
        self.assertEqual(r2.get_responder_id(), u1.get_id())
        self.assertEqual(r2.get_question_id(), q1.get_id())
        self.assertEqual(r2.get_response_text(), "lololol")
        self.assertEqual(r2.get_choice_ids(), [])

        # Check response_id was added to User.response_ids
        self.assertEqual(u1.get_response_ids(), [r1.get_id(), r2.get_id()])

        # Check response_id was added to Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r1.get_id(), r2.get_id()])

        q2 = p.create_question(u1, "trick?", "free")
        c1 = p.create_choice(q1, "choice 1")
        c2 = p.create_choice(q2, "choice 2")
        r3 = p.create_response(u1, q1, response_text="k", choice_ids=[c1.get_id()])
        self.assertEqual(r3.get_id(), 3)
        self.assertEqual(r3.get_responder_id(), u1.get_id())
        self.assertEqual(r3.get_question_id(), q1.get_id())
        self.assertEqual(r3.get_response_text(), "k")
        self.assertEqual(r3.get_choice_ids(), [c1.get_id()])

        # Check response_id was added to User.response_ids
        self.assertEqual(u1.get_response_ids(), [r1.get_id(), r2.get_id(), r3.get_id()])

        # Check response_id was added to Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r1.get_id(), r2.get_id(), r3.get_id()])

        # Test adding choice to response with mis-matching question_id
        with self.assertRaises(InvalidQuestionIdError):
            p.create_response(u1, q1, response_text="k", choice_ids=[c1.get_id(), c2.get_id()])

        # Test creation with non-existant responders (User)
        with self.assertRaises(UserNotFoundError):
            p.create_response(User("nonexistant user"), q1)

        with self.assertRaises(UserNotFoundError):
            p.create_response(1234, q1)

        # Test creation with non-existant questions
        with self.assertRaises(QuestionNotFoundError):
            p.create_response(u1, 1234)

        with self.assertRaises(QuestionNotFoundError):
            p.create_response(u1, Question(1, "lol?", "free"))

    def test_create_survey(self):
        u1 = p.register_user("Bob")
        s = p.create_survey("survey 1", u1)
        self.assertEqual(s.get_id(), 1)
        self.assertEqual(s.get_name(), "survey 1")
        self.assertEqual(s.get_owner_id(), u1.get_id())
        self.assertEqual(s.get_event_id(), None)
        self.assertEqual(s.get_question_ids(), [])

        q1 = p.create_question(u1, "q1", "free")
        q2 = p.create_question(u1.get_id(), "q2", "free")
        e1 = p.create_event("event 1", u1)
        s2 = p.create_survey("s", u1, question_ids=[q1.get_id(), q2.get_id()], event_obj=e1.get_id())
        self.assertEqual(s2.get_name(), "s")
        self.assertEqual(s2.get_id(), 2)
        self.assertEqual(s2.get_owner_id(), u1.get_id())
        self.assertEqual(s2.get_event_id(), 1)
        self.assertEqual(s2.get_question_ids(), [q1.get_id(), q2.get_id()])

        # Check User.survey_ids was updated
        self.assertEqual(u1.get_survey_ids(), [s.get_id(), s2.get_id()])

        # Check Event.survey_ids was updated
        self.assertEqual(e1.get_survey_ids(), [s2.get_id()])

        # Check Question.survey_id was updated
        self.assertEqual(q1.get_survey_id(), s2.get_id())
        self.assertEqual(q2.get_survey_id(), s2.get_id())

        # Test creation with owners that don't exist
        with self.assertRaises(UserNotFoundError):
            p.create_survey("s1", 999)

        with self.assertRaises(UserNotFoundError):
            p.create_survey("s1", 1234, event_obj=1234)

        with self.assertRaises(UserNotFoundError):
            p.create_survey("s1", User("lol"), question_ids=[q1.get_id()])

        # Test creation with questions that don't (all) exist
        with self.assertRaises(QuestionNotFoundError):
            p.create_survey("in_s", u1, question_ids=[q1.get_id(), Question(31, "?", "free")])

        with self.assertRaises(QuestionNotFoundError):
            p.create_survey("in_s", u1, question_ids=[Question(11, ".", "free")])

        with self.assertRaises(QuestionNotFoundError):
            q1_inv = Question(24, ".", "free")
            q2_inv = Question(999, "?", "free")
            p.create_survey("in_s", u1, question_ids=[q1_inv, q2_inv], event_obj=e1.get_id())

        # Test creation with events that don't exist
        with self.assertRaises(EventNotFoundError):
            p.create_survey("s1", u1, event_obj=1234)

        with self.assertRaises(EventNotFoundError):
            p.create_survey("s1", u1, event_obj="asdf")

        with self.assertRaises(EventNotFoundError):
            p.create_survey("s1", u1, event_obj=Event("nonexistant event", u1.get_id()))

    def test_delete_choice(self):
        u1 = p.register_user("bob")
        q = p.create_question(u1, "Hello?", "free")
        ch = p.create_choice(q, "choice 1")
        self.assertEqual(q.get_allowed_choice_ids(), [ch.get_id()])

        ch2 = p.create_choice(q, "choice 2")
        self.assertEqual(q.get_allowed_choice_ids(), [ch.get_id(), ch2.get_id()])

        p.delete_choice(ch)
        self.assertEqual(q.get_allowed_choice_ids(), [ch2.get_id()])
        self.assertIsNone(p.db_interface.get_obj(ch, Choice))

        p.delete_choice(ch2)
        self.assertEqual(q.get_allowed_choice_ids(), [])
        self.assertIsNone(p.db_interface.get_obj(ch, Choice))
        self.assertIsNone(p.db_interface.get_obj(ch2, Choice))

        q = p.create_question(1, "write something", "free")
        p.create_choice(q, "choice 1.3")

        # Test deletion with choices that don't exist
        with self.assertRaises(ChoiceNotFoundError):
            p.delete_choice(ch2)

        with self.assertRaises(ChoiceNotFoundError):
            p.delete_choice(Choice(333, "lalala"))

    def test_delete_question(self):
        u1 = p.register_user("user1")
        u2 = p.register_user("second user")
        q = p.create_question(u1.get_id(), "Hello?", "free")
        self.assertEqual(u1.get_question_ids(), [q.get_id()])

        p.delete_question(q)

        # Check Choice object was deleted
        self.assertIsNone(p.db_interface.get_obj(1, Question))

        # Check User.question_ids was updated
        self.assertEqual(u1.get_question_ids(), [])

        s = p.create_survey("SOME COOL SURVEY", u2)
        self.assertEqual(s.get_question_ids(), [])
        q1 = p.create_question(u2.get_id(), "question 1", "free", survey_obj=s)
        self.assertEqual(u2.get_question_ids(), [q1.get_id()])

        c1 = p.create_choice(q1, "choice 1")
        c2 = p.create_choice(q1, "choice 2")

        p.delete_question(q1)

        # Check Choice objects were deleted
        self.assertIsNone(p.db_interface.get_obj(c1, Choice))
        self.assertIsNone(p.db_interface.get_obj(c2, Choice))

        # Check User.question_ids was updated
        self.assertEqual(u1.get_question_ids(), [])
        self.assertEqual(u2.get_question_ids(), [])

        # Check Survey.question_ids was updated
        self.assertEqual(s.get_question_ids(), [])

        q2 = p.create_question(u1, "the sec0nd question", "free", survey_obj=s)
        self.assertEqual(u1.get_question_ids(), [q2.get_id()])
        self.assertEqual(u2.get_question_ids(), [])

        c1 = p.create_choice(q2, "choice 1.2")
        c2 = p.create_choice(q2, "choice 2.2")

        r1 = p.create_response(u1, q2, "lololol")
        r2 = p.create_response(u2, q2, "lololol")

        p.delete_question(q2)

        # Check Choice objects were deleted
        self.assertIsNone(p.db_interface.get_obj(c1, Choice))
        self.assertIsNone(p.db_interface.get_obj(c2, Choice))

        # Check User.question_ids was updated
        self.assertEqual(u1.get_question_ids(), [])
        self.assertEqual(u2.get_question_ids(), [])

        # Check Response objects were deleted
        self.assertIsNone(p.db_interface.get_obj(r1, Response))
        self.assertIsNone(p.db_interface.get_obj(r2, Response))

        # Check Survey.question_ids was updated
        self.assertEqual(s.get_question_ids(), [])

        # Test creation with invalid question types
        with self.assertRaises(InvalidQuestionTypeError):
            p.create_question(89, "invalid question", "invalid")

        with self.assertRaises(InvalidQuestionTypeError):
            p.create_question(12, "invalid question", 3)

        with self.assertRaises(InvalidQuestionTypeError):
            p.create_question(42, "invalid question", ["free"])

        # Test deletion of questions that don't exist
        with self.assertRaises(QuestionNotFoundError):
            p.delete_question(q2)

        with self.assertRaises(QuestionNotFoundError):
            p.delete_question(Question(1, "lol?", "free"))

    def test_delete_response(self):
        u1 = p.register_user("USER 1")
        self.assertEqual(u1.get_response_ids(), [])

        q1 = p.create_question(u1, "QUESTION?", "free")
        r1 = p.create_response(u1, q1)

        # Check response_id was added to Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r1.get_id()])

        r2 = p.create_response(u1, q1, response_text="lololol")
        # Check User.response_ids was updated
        self.assertEqual(u1.get_response_ids(), [r1.get_id(), r2.get_id()])

        # Check response_id was added to Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r1.get_id(), r2.get_id()])

        p.delete_response(r2)
        self.assertEqual(u1.get_response_ids(), [r1.get_id()])
        self.assertIsNone(p.db_interface.get_obj(r2, Response))

        # Check response_id was removed from Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r1.get_id()])

        c1 = p.create_choice(q1, "choice 1")
        c2 = p.create_choice(q1, "choice 2")
        r3 = p.create_response(u1, q1, response_text="k", choice_ids=[c1.get_id(), c2.get_id()])

        # Check response_id was added to Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r1.get_id(), r3.get_id()])

        p.delete_response(r1)
        self.assertIsNone(p.db_interface.get_obj(r1, Response))

        # Check User.response_ids was updated
        self.assertEqual(u1.get_response_ids(), [r3.get_id()])

        # Check response_id was removed from Question.response_ids
        self.assertEqual(q1.get_response_ids(), [r3.get_id()])

        p.delete_response(r3)
        self.assertIsNone(p.db_interface.get_obj(r1, Response))

        # Check User.response_ids was updated
        self.assertEqual(u1.get_response_ids(), [])

        # Check response_id was removed from Question.response_ids
        self.assertEqual(q1.get_response_ids(), [])

        # Test deletion with non-existant responses
        with self.assertRaises(ResponseNotFoundError):
            p.delete_response(r3)

        with self.assertRaises(ResponseNotFoundError):
            p.delete_response(Response(1, 3))

    def test_delete_survey(self):
        u1 = p.register_user("Bob")
        u2 = p.register_user("Jane")
        s = p.create_survey("survey 1", u1)
        self.assertEqual(u1.get_survey_ids(), [s.get_id()])

        p.delete_survey(s)
        # Check User.survey_ids was updated
        self.assertEqual(u1.get_survey_ids(), [])
        self.assertIsNone(p.db_interface.get_obj(s, Survey))


        q1 = p.create_question(u1, "q1", "free")
        q2 = p.create_question(u1.get_id(), "q2", "free")
        c1 = p.create_choice(q1, "choice 1")
        r1 = p.create_response(u1, q1)
        r2 = p.create_response(u2, q1, choice_ids=[c1.get_id()])
        r3 = p.create_response(u2, q2)
        e1 = p.create_event("event 1", u1)
        s = p.create_survey("s", u1, question_ids=[q1.get_id(), q2.get_id()], event_obj=e1.get_id())
        self.assertEqual(u1.get_survey_ids(), [s.get_id()])

        p.delete_survey(s)
        # Check User.survey_ids was updated
        self.assertEqual(u1.get_survey_ids(), [])
        self.assertIsNone(p.db_interface.get_obj(s, Survey))

        # Check questions were deleted
        self.assertIsNone(p.db_interface.get_obj(q1, Question))
        self.assertIsNone(p.db_interface.get_obj(q2, Question))

        # Check responses were deleted
        self.assertIsNone(p.db_interface.get_obj(r1, Response))
        self.assertIsNone(p.db_interface.get_obj(r2, Response))
        self.assertIsNone(p.db_interface.get_obj(r3, Response))

        # Test deletion with non-existant surveys
        with self.assertRaises(SurveyNotFoundError):
            p.delete_survey(Survey("lol", 3))

        with self.assertRaises(SurveyNotFoundError):
            p.delete_survey(9923)

    def test_get_responder(self):
        u1 = p.register_user("user 1")
        u2 = p.register_user("user 2")

        q1 = p.create_question(u1, "question 1", "free")
        c1 = p.create_choice(q1, "choice 1")

        r1 = p.create_response(u1, q1, "ceebs")
        r2 = p.create_response(u2, q1, "nup", choice_ids=[c1.get_id()])

        self.assertEqual(p.get_responder(r1), u1)
        self.assertEqual(p.get_responder(r2), u2)

        # Test getting responder of response that doesn't exist
        with self.assertRaises(ResponseNotFoundError):
            p.get_responder(1234)

        with self.assertRaises(ResponseNotFoundError):
            p.get_responder(Response(1, 2))

    def test_get_response_choices(self):
        u1 = p.register_user("user 1")
        u2 = p.register_user("user 2")

        q1 = p.create_question(u1, "question 1", "free")
        c1 = p.create_choice(q1, "choice 1")
        c2 = p.create_choice(q1, "choice 2")

        r1 = p.create_response(u1, q1, "ceebs")
        r2 = p.create_response(u2, q1, "nup", choice_ids=[c1.get_id()])
        r2.add_choice_id(c2)
        p.db_interface.update(r2)

        self.assertEqual(p.get_response_choices(r1), [])
        self.assertEqual(p.get_response_choices(r2), [c1, c2])

        # Test getting from a response that doesn't exist
        with self.assertRaises(ResponseNotFoundError):
            p.get_responder(1234)

        with self.assertRaises(ResponseNotFoundError):
            p.get_responder(Response(1, 2))

    def test_get_allowed_choices(self):
        u1 = p.register_user("user 1")

        q1 = p.create_question(u1, "question 1", "free")
        self.assertEqual(p.get_allowed_choices(q1), [])
        c1 = p.create_choice(q1, "choice 1")
        c2 = p.create_choice(q1, "choice 2")

        self.assertEqual(p.get_allowed_choices(q1), [c1, c2])

        # Test getting from a question that doesn't exist
        with self.assertRaises(QuestionNotFoundError):
            p.get_allowed_choices(9123)

        with self.assertRaises(QuestionNotFoundError):
            p.get_allowed_choices(Question(1, "question?", "free"))

    def test_get_responses(self):
        u1 = p.register_user("user 1")
        u2 = p.register_user("user 2")

        q1 = p.create_question(u1, "question 1", "free")
        self.assertEqual(p.get_responses(q1), [])
        self.assertEqual(p.get_responses(u1), [])
        self.assertEqual(p.get_responses(u2), [])

        c1 = p.create_choice(q1, "choice 1")
        r1 = p.create_response(u1, q1, "ceebs")
        r2 = p.create_response(u2, q1, "nup", choice_ids=[c1.get_id()])
        self.assertEqual(p.get_responses(q1), [r1, r2])
        self.assertEqual(p.get_responses(u1), [r1])
        self.assertEqual(p.get_responses(u2), [r2])

        # Test getting from a question that doesn't exist
        with self.assertRaises(QuestionNotFoundError):
            p.get_allowed_choices(9123)

        with self.assertRaises(QuestionNotFoundError):
            p.get_allowed_choices(Question(1, "question?", "free"))

    def test_get_questions(self):
        u1 = p.register_user("user 1")
        q1 = p.create_question(u1, "question 1", "free")
        s1 = p.create_survey("survey 1", u1, question_ids=[q1.get_id()])
        self.assertEqual(p.get_questions(s1), [q1])
        self.assertEqual(p.get_questions(u1), [q1])

        q2 = p.create_question(u1, "lol?", "free", survey_obj=s1)
        self.assertEqual(p.get_questions(s1), [q1, q2])
        self.assertEqual(p.get_questions(u1), [q1, q2])

        q3 = p.create_question(u1, "k then?", "free")
        s1.add_question_id(q3)
        p.db_interface.update(s1)
        self.assertEqual(p.get_questions(s1), [q1, q2, q3])
        self.assertEqual(p.get_questions(u1), [q1, q2, q3])

        # Test getting from invalid obj type
        with self.assertRaises(TypeError):
            p.get_questions(9123)

        with self.assertRaises(TypeError):
            p.get_questions("asdf")

    def test_get_owner(self):
        u1 = p.register_user("User 1")
        u2 = p.register_user("u2")
        u3 = p.register_user("3rd")

        # Test event
        e1 = p.create_event("event 1", u1)
        e2 = p.create_event("2nd event", u2, location="lol world")

        self.assertEqual(p.get_owner(e1), u1)
        self.assertEqual(p.get_owner(e2), u2)

        # Test surveys
        s1 = p.create_survey("s1", u2)
        s2 = p.create_survey("survey 2", u3)
        self.assertEqual(p.get_owner(s1), u2)
        self.assertEqual(p.get_owner(s2), u3)

        # Test questions
        q1 = p.create_question(u3, "question?", "free")
        q2 = p.create_question(u1, "question?", "free", survey_obj=s1)
        self.assertEqual(p.get_owner(q1), u3)
        self.assertEqual(p.get_owner(q2), u1)

        # Test invalid types
        with self.assertRaises(TypeError):
            p.get_owner(u1)

        with self.assertRaises(TypeError):
            p.get_owner("lalala")

        with self.assertRaises(TypeError):
            p.get_owner(3012)

    def test_get_surveys(self):
        # Create some users
        u1 = p.register_user("User 1")
        u2 = p.register_user("u2")
        u3 = p.register_user("3rd")

        # Create some events
        e1 = p.create_event("event 1", 1)
        e2 = p.create_event("event 2", 2, location="location 2")
        e3 = p.create_event("event 3", 2, time=datetime.today() + timedelta(days=10))

        self.assertEqual(p.get_surveys(u1), [])
        self.assertEqual(p.get_surveys(u2), [])
        self.assertEqual(p.get_surveys(u3), [])

        self.assertEqual(p.get_surveys(e1), [])
        self.assertEqual(p.get_surveys(e2), [])
        self.assertEqual(p.get_surveys(e3), [])

        # Create some surveys
        s1 = p.create_survey("survey 1", u1)
        self.assertEqual(p.get_surveys(u1), [s1])
        self.assertEqual(p.get_surveys(u2), [])
        self.assertEqual(p.get_surveys(u3), [])

        self.assertEqual(p.get_surveys(e1), [])
        self.assertEqual(p.get_surveys(e2), [])
        self.assertEqual(p.get_surveys(e3), [])

        s2 = p.create_survey("survey 2", u1, event_obj=e1)
        self.assertEqual(p.get_surveys(u1), [s1, s2])
        self.assertEqual(p.get_surveys(u2), [])
        self.assertEqual(p.get_surveys(u3), [])

        self.assertEqual(p.get_surveys(e1), [s2])
        self.assertEqual(p.get_surveys(e2), [])
        self.assertEqual(p.get_surveys(e3), [])

        s3 = p.create_survey("survey 3", u2, event_obj=e1)
        self.assertEqual(p.get_surveys(u1), [s1, s2])
        self.assertEqual(p.get_surveys(u2), [s3])
        self.assertEqual(p.get_surveys(u3), [])

        self.assertEqual(p.get_surveys(e1), [s2, s3])
        self.assertEqual(p.get_surveys(e2), [])
        self.assertEqual(p.get_surveys(e3), [])

        s4 = p.create_survey("survey 4", u2, event_obj=e2)
        self.assertEqual(p.get_surveys(u1), [s1, s2])
        self.assertEqual(p.get_surveys(u2), [s3, s4])
        self.assertEqual(p.get_surveys(u3), [])

        self.assertEqual(p.get_surveys(e1), [s2, s3])
        self.assertEqual(p.get_surveys(e2), [s4])
        self.assertEqual(p.get_surveys(e3), [])

        s5 = p.create_survey("survey 4", u3, event_obj=e3)
        self.assertEqual(p.get_surveys(u1), [s1, s2])
        self.assertEqual(p.get_surveys(u2), [s3, s4])
        self.assertEqual(p.get_surveys(u3), [s5])

        self.assertEqual(p.get_surveys(e1), [s2, s3])
        self.assertEqual(p.get_surveys(e2), [s4])
        self.assertEqual(p.get_surveys(e3), [s5])

# Generate empty test database
conn = sqlite3.connect(porg_config.DB_NAME)
c = conn.cursor()
generate_db(c)

# Create PorgWrapper
p = PorgWrapper()

if __name__ == '__main__':
    unittest.main()

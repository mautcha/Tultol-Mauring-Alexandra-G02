from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Mall, Floor, Store, SavedStore


class MallStoreDirectoryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.shopper = User.objects.create_user(
            username='shopper1', email='s1@example.com', password='Password123!'
        )
        self.admin = User.objects.create_user(
            username='admin1', email='a1@example.com', password='Password123!', is_staff=True
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        self.mall = Mall.objects.create(
            name='SM Seaside City Cebu',
            city='Cebu City',
            address='SRP, Cebu City',
            created_by=self.admin,
        )
        self.floor = Floor.objects.create(
            mall=self.mall,
            floor_number=0,
            name='Ground Floor',
            map_notes='Near Mountain Wing',
            created_by=self.admin,
        )
        self.store = Store.objects.create(
            mall=self.mall,
            floor=self.floor,
            name='National Book Store',
            category='services',
            unit_code='GF-104',
            landmark_directions='Beside Cube Wing Entrance',
            created_by=self.admin,
        )

    def test_directory_requires_login(self):
        resp = self.client.get(reverse('directory:store_list'))
        self.assertRedirects(resp, f"{reverse('accounts:login')}?next={reverse('directory:store_list')}")

    def test_shopper_can_search_and_view_store_but_cannot_add_or_edit(self):
        self.client.login(username='shopper1', password='Password123!')

        list_resp = self.client.get(reverse('directory:store_list'), {'q': 'National'})
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, 'National Book Store')

        detail_resp = self.client.get(reverse('directory:store_detail', args=[self.store.pk]))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, 'Beside Cube Wing Entrance')

        # Shopper blocked from Admin CRUD routes
        blocked = self.client.get(reverse('directory:store_create'), follow=True)
        self.assertRedirects(blocked, reverse('dashboard:shopper_dashboard'))

    def test_admin_crud_mall_floor_store_and_validation(self):
        self.client.login(username='admin1', password='Password123!')

        # Create Mall
        resp = self.client.post(reverse('directory:mall_create'), {
            'name': 'Ayala Center Cebu',
            'city': 'Cebu City',
            'address': 'Cebu Business Park',
            'opening_hours': '10:00 AM - 9:00 PM',
        }, follow=True)
        self.assertRedirects(resp, reverse('directory:mall_list'))
        ayala = Mall.objects.get(name='Ayala Center Cebu')
        self.assertEqual(ayala.created_by, self.admin)

        # Create Floor
        resp = self.client.post(reverse('directory:floor_create'), {
            'mall': ayala.pk,
            'floor_number': 1,
            'name': '2nd Floor',
            'map_notes': 'Terraces wing',
        }, follow=True)
        self.assertRedirects(resp, reverse('directory:mall_list'))
        ayala_f2 = Floor.objects.get(mall=ayala, floor_number=1)

        # Create Store
        resp = self.client.post(reverse('directory:store_create'), {
            'floor': ayala_f2.pk,
            'name': 'Jollibee',
            'category': 'dining',
            'unit_code': '2f-201',
            'landmark_directions': 'Near The Terraces escalator',
            'operating_hours': '10:00 AM - 9:00 PM',
            'is_open': True,
        }, follow=True)
        self.assertRedirects(resp, reverse('directory:store_list'))
        jollibee = Store.objects.get(name='Jollibee')
        self.assertEqual(jollibee.unit_code, '2F-201')
        self.assertEqual(jollibee.mall, ayala)

        # Duplicate unit_code on same floor rejected
        dup_resp = self.client.post(reverse('directory:store_create'), {
            'floor': ayala_f2.pk,
            'name': 'Another Store',
            'category': 'dining',
            'unit_code': '2F-201',
            'landmark_directions': 'Somewhere',
            'operating_hours': '10:00 AM - 9:00 PM',
            'is_open': True,
        })
        self.assertEqual(dup_resp.status_code, 200)
        self.assertIn('unit_code', dup_resp.context['form'].errors)

        # Update Store
        upd_resp = self.client.post(reverse('directory:store_update', args=[jollibee.pk]), {
            'floor': ayala_f2.pk,
            'name': 'Jollibee Terraces',
            'category': 'dining',
            'unit_code': '2F-201',
            'landmark_directions': 'Across cinema lobby',
            'operating_hours': '9:00 AM - 10:00 PM',
            'is_open': True,
        }, follow=True)
        self.assertRedirects(upd_resp, reverse('directory:store_detail', args=[jollibee.pk]))
        jollibee.refresh_from_db()
        self.assertEqual(jollibee.name, 'Jollibee Terraces')

        # Delete Store
        del_resp = self.client.post(reverse('directory:store_delete', args=[jollibee.pk]), follow=True)
        self.assertRedirects(del_resp, reverse('directory:store_list'))
        self.assertFalse(Store.objects.filter(pk=jollibee.pk).exists())

    def test_shopper_saved_stores_crud_and_ownership(self):
        other_shopper = User.objects.create_user(
            username='shopper2', email='s2@example.com', password='Password123!'
        )
        self.client.login(username='shopper1', password='Password123!')

        # Save store (Create)
        create_resp = self.client.post(reverse('directory:saved_create', args=[self.store.pk]), {
            'note': 'Buy art supplies',
        }, follow=True)
        self.assertRedirects(create_resp, reverse('directory:store_detail', args=[self.store.pk]))
        saved = SavedStore.objects.get(user=self.shopper, store=self.store)
        self.assertEqual(saved.note, 'Buy art supplies')

        # Duplicate save does not create second row
        self.client.post(reverse('directory:saved_create', args=[self.store.pk]), {'note': 'Duplicate'})
        self.assertEqual(SavedStore.objects.filter(user=self.shopper, store=self.store).count(), 1)

        # List own saved stores (Read)
        list_resp = self.client.get(reverse('directory:saved_list'))
        self.assertContains(list_resp, 'National Book Store')
        self.assertContains(list_resp, 'Buy art supplies')

        # Update note (Update)
        upd_resp = self.client.post(reverse('directory:saved_update', args=[saved.pk]), {
            'note': 'Pick up notebooks at 4 PM',
        }, follow=True)
        self.assertRedirects(upd_resp, reverse('directory:saved_list'))
        saved.refresh_from_db()
        self.assertEqual(saved.note, 'Pick up notebooks at 4 PM')

        # Another user cannot view/edit/delete shopper1's bookmark
        self.client.logout()
        self.client.login(username='shopper2', password='Password123!')
        self.assertEqual(self.client.get(reverse('directory:saved_update', args=[saved.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('directory:saved_delete', args=[saved.pk])).status_code, 404)
        other_list = self.client.get(reverse('directory:saved_list'))
        self.assertNotContains(other_list, 'National Book Store')

        # Original owner can delete (Delete)
        self.client.logout()
        self.client.login(username='shopper1', password='Password123!')
        del_resp = self.client.post(reverse('directory:saved_delete', args=[saved.pk]), follow=True)
        self.assertRedirects(del_resp, reverse('directory:saved_list'))
        self.assertFalse(SavedStore.objects.filter(pk=saved.pk).exists())

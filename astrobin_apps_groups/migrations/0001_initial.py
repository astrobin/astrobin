# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Group'
        db.create_table(u'astrobin_apps_groups_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('date_updated', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_group_set', to=orm['auth.User'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='owned_group_set', to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('moderated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('autosubmission', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('forum', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='group', unique=True, null=True, to=orm['pybb.Forum'])),
        ))
        db.send_create_signal('astrobin_apps_groups', ['Group'])

        # Adding M2M table for field moderators on 'Group'
        db.create_table(u'astrobin_apps_groups_group_moderators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['astrobin_apps_groups.group'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'astrobin_apps_groups_group_moderators', ['group_id', 'user_id'])

        # Adding M2M table for field members on 'Group'
        db.create_table(u'astrobin_apps_groups_group_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['astrobin_apps_groups.group'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'astrobin_apps_groups_group_members', ['group_id', 'user_id'])

        # Adding M2M table for field invited_users on 'Group'
        db.create_table(u'astrobin_apps_groups_group_invited_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['astrobin_apps_groups.group'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'astrobin_apps_groups_group_invited_users', ['group_id', 'user_id'])

        # Adding M2M table for field join_requests on 'Group'
        db.create_table(u'astrobin_apps_groups_group_join_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['astrobin_apps_groups.group'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'astrobin_apps_groups_group_join_requests', ['group_id', 'user_id'])

        # Adding M2M table for field images on 'Group'
        db.create_table(u'astrobin_apps_groups_group_images', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['astrobin_apps_groups.group'], null=False)),
            ('image', models.ForeignKey(orm['astrobin.image'], null=False))
        ))
        db.create_unique(u'astrobin_apps_groups_group_images', ['group_id', 'image_id'])


    def backwards(self, orm):
        # Deleting model 'Group'
        db.delete_table(u'astrobin_apps_groups_group')

        # Removing M2M table for field moderators on 'Group'
        db.delete_table('astrobin_apps_groups_group_moderators')

        # Removing M2M table for field members on 'Group'
        db.delete_table('astrobin_apps_groups_group_members')

        # Removing M2M table for field invited_users on 'Group'
        db.delete_table('astrobin_apps_groups_group_invited_users')

        # Removing M2M table for field join_requests on 'Group'
        db.delete_table('astrobin_apps_groups_group_join_requests')

        # Removing M2M table for field images on 'Group'
        db.delete_table('astrobin_apps_groups_group_images')


    models = {
        'astrobin.accessory': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Accessory', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.camera': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Camera', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'pixel_size': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'sensor_height': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'sensor_width': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.commercialgear': {
            'Meta': {'ordering': "['created']", 'object_name': 'CommercialGear'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_ar': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_de': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_el': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_fi': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_fr': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_it': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_ja': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_nl': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_pl': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_pt_BR': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_ru': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_sq': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_tr': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'featured_gear'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['astrobin.Image']"}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'producer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commercial_gear'", 'to': u"orm['auth.User']"}),
            'proper_make': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'proper_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_ar': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_de': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_el': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_en': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_es': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_fi': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_fr': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_it': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_ja': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_nl': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_pl': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_pt_BR': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_ru': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_sq': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'tagline_tr': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'astrobin.filter': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Filter', '_ormbases': ['astrobin.Gear']},
            'bandwidth': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.focalreducer': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'FocalReducer', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'})
        },
        'astrobin.gear': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Gear'},
            'commercial': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'base_gear'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['astrobin.CommercialGear']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'make': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.Gear']", 'null': 'True'}),
            'moderator_fixed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'retailed': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['astrobin.RetailedGear']", 'symmetrical': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'astrobin.image': {
            'Meta': {'ordering': "('-uploaded', '-id')", 'object_name': 'Image'},
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Accessory']", 'null': 'True', 'blank': 'True'}),
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'animated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Filter']", 'null': 'True', 'blank': 'True'}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']", 'null': 'True', 'blank': 'True'}),
            'guiding_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'guiding_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guiding_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'h': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_file': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True'}),
            'imaging_cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'imaging_telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'imaging_telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'is_final': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_wip': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'license': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'link_to_fits': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['astrobin.Location']", 'symmetrical': 'False'}),
            'moderated_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images_moderated'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'moderated_when': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'moderator_decision': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Mount']", 'null': 'True', 'blank': 'True'}),
            'objects_in_field': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'plot_is_overlay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['astrobin.Software']", 'null': 'True', 'blank': 'True'}),
            'solar_system_main_subject': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject_type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'w': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'watermark': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'watermark_opacity': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'watermark_position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'watermark_size': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'watermark_text': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'astrobin.location': {
            'Meta': {'object_name': 'Location'},
            'altitude': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'country': ('astrobin.fields.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat_deg': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'lat_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lat_sec': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lat_side': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'lon_deg': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'lon_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lon_sec': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'lon_side': ('django.db.models.fields.CharField', [], {'default': "'E'", 'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['astrobin.UserProfile']", 'null': 'True'})
        },
        'astrobin.mount': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Mount', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'max_payload': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'pe': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'})
        },
        'astrobin.retailedgear': {
            'Meta': {'ordering': "['created']", 'object_name': 'RetailedGear'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'EUR'", 'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'retailer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'retailed_gear'", 'to': u"orm['auth.User']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'astrobin.software': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Software', '_ormbases': ['astrobin.Gear']},
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.telescope': {
            'Meta': {'ordering': "('-updated',)", 'object_name': 'Telescope', '_ormbases': ['astrobin.Gear']},
            'aperture': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'focal_length': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            u'gear_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['astrobin.Gear']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'astrobin.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'about': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'accessories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'accessories'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Accessory']"}),
            'autosubscribe': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'avatar': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'cameras': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'cameras'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Camera']"}),
            'company_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'company_website': ('django.db.models.fields.URLField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'default_frontpage_section': ('django.db.models.fields.CharField', [], {'default': "'personal'", 'max_length': '16'}),
            'default_gallery_sorting': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'default_license': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'default_watermark': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_watermark_opacity': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'default_watermark_position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'default_watermark_size': ('django.db.models.fields.CharField', [], {'default': "'M'", 'max_length': '1'}),
            'default_watermark_text': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'exclude_from_competitions': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'filters'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Filter']"}),
            'focal_reducers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'focal_reducers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.FocalReducer']"}),
            'hobbies': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'mounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'mounts'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Mount']"}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'premium_counter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'real_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'receive_forum_emails': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'retailer_country': ('astrobin.fields.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'seen_realname': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_signatures': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            'signature_html': ('django.db.models.fields.TextField', [], {'max_length': '1054', 'blank': 'True'}),
            'software': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'software'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Software']"}),
            'telescopes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'telescopes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Telescope']"}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'astrobin_apps_groups.group': {
            'Meta': {'ordering': "['-date_created']", 'object_name': 'Group'},
            'autosubmission': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_group_set'", 'to': u"orm['auth.User']"}),
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'forum': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'group'", 'unique': 'True', 'null': 'True', 'to': u"orm['pybb.Forum']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'images': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'part_of_group_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['astrobin.Image']"}),
            'invited_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'invited_group_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'join_requests': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'join_requested_group_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'joined_group_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'moderated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'moderated_group_set'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owned_group_set'", 'to': u"orm['auth.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'pybb.category': {
            'Meta': {'ordering': "[u'position']", 'object_name': 'Category'},
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'pybb.forum': {
            'Meta': {'ordering': "[u'position']", 'unique_together': "((u'category', u'slug'),)", 'object_name': 'Forum'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'forums'", 'to': u"orm['pybb.Category']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'headline': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'child_forums'", 'null': 'True', 'to': u"orm['pybb.Forum']"}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'readed_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'readed_forums'", 'symmetrical': 'False', 'through': u"orm['pybb.ForumReadTracker']", 'to': u"orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'topic_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'pybb.forumreadtracker': {
            'Meta': {'unique_together': "((u'user', u'forum'),)", 'object_name': 'ForumReadTracker'},
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pybb.Forum']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time_stamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['astrobin_apps_groups']
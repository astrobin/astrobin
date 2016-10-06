# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PlateSolvingSettings'
        db.create_table(u'astrobin_apps_platesolving_platesolvingsettings', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('blind', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('scale_units', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('scale_min', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=3, blank=True)),
            ('scale_max', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=3, blank=True)),
            ('center_ra', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=3, blank=True)),
            ('center_dec', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=3, blank=True)),
            ('radius', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=3, blank=True)),
        ))
        db.send_create_signal(u'astrobin_apps_platesolving', ['PlateSolvingSettings'])

        # Adding field 'Solution.settings'
        db.add_column(u'astrobin_apps_platesolving_solution', 'settings',
                      self.gf('django.db.models.fields.related.OneToOneField')(related_name='solution', unique=True, null=True, to=orm['astrobin_apps_platesolving.PlateSolvingSettings']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'PlateSolvingSettings'
        db.delete_table(u'astrobin_apps_platesolving_platesolvingsettings')

        # Deleting field 'Solution.settings'
        db.delete_column(u'astrobin_apps_platesolving_solution', 'settings_id')


    models = {
        u'astrobin_apps_platesolving.platesolvingsettings': {
            'Meta': {'object_name': 'PlateSolvingSettings'},
            'blind': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'center_dec': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '3', 'blank': 'True'}),
            'center_ra': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '3', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'radius': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '3', 'blank': 'True'}),
            'scale_max': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '3', 'blank': 'True'}),
            'scale_min': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '3', 'blank': 'True'}),
            'scale_units': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'})
        },
        'astrobin_apps_platesolving.solution': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Solution'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'dec': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.TextField', [], {}),
            'objects_in_field': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'orientation': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'pixscale': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'ra': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'radius': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3', 'blank': 'True'}),
            'settings': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'solution'", 'unique': 'True', 'null': 'True', 'to': u"orm['astrobin_apps_platesolving.PlateSolvingSettings']"}),
            'skyplot_zoom1': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'submission_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['astrobin_apps_platesolving']
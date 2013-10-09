# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Solution'
        db.create_table('astrobin_apps_platesolving_solution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('job_success', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('objects_in_field', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('ra_center_hms', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True)),
            ('dec_center_dms', self.gf('django.db.models.fields.CharField')(max_length=13, null=True, blank=True)),
            ('pixscale', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10, blank=True)),
            ('orientation', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10, blank=True)),
            ('fieldw', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10, blank=True)),
            ('fieldh', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=14, decimal_places=10, blank=True)),
            ('fieldunits', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
        ))
        db.send_create_signal('astrobin_apps_platesolving', ['Solution'])


    def backwards(self, orm):
        
        # Deleting model 'Solution'
        db.delete_table('astrobin_apps_platesolving_solution')


    models = {
        'astrobin_apps_platesolving.solution': {
            'Meta': {'object_name': 'Solution'},
            'dec_center_dms': ('django.db.models.fields.CharField', [], {'max_length': '13', 'null': 'True', 'blank': 'True'}),
            'fieldh': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'fieldunits': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'fieldw': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_success': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'objects_in_field': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'orientation': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'pixscale': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '14', 'decimal_places': '10', 'blank': 'True'}),
            'ra_center_hms': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['astrobin_apps_platesolving']

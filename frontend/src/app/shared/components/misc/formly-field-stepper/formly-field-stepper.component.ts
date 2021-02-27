import { Component } from "@angular/core";
import { FieldType, FormlyFieldConfig } from "@ngx-formly/core";
import { TranslateService } from "@ngx-translate/core";
import { STEP_STATE } from "ng-wizard";

@Component({
  selector: "astrobin-formly-field-stepper",
  templateUrl: "./formly-field-stepper.component.html",
  styleUrls: ["./formly-field-stepper.component.scss"]
})
export class FormlyFieldStepperComponent extends FieldType {
  constructor(public translateService: TranslateService) {
    super();
  }

  getStepTitle(field: FormlyFieldConfig, stepNumber: number): string {
    let title = this.translateService.instant("Step {{ stepNumber }}", { stepNumber });
    if (!this.isValid(field)) {
      title += " (!)";
    }

    return title;
  }

  isValid(field: FormlyFieldConfig) {
    if (field.key) {
      return field.formControl.valid;
    }

    return field.fieldGroup.every(f => this.isValid(f));
  }

  getState(field: FormlyFieldConfig): STEP_STATE {
    if (!this.isValid(field)) {
      return STEP_STATE.error;
    }

    return STEP_STATE.normal;
  }
}

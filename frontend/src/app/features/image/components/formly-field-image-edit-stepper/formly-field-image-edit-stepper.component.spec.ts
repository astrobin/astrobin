import { ComponentFixture, TestBed } from "@angular/core/testing";

import { FormlyFieldImageEditStepperComponent } from "./formly-field-image-edit-stepper.component";

describe("FormlyFieldStepperComponent", () => {
  let component: FormlyFieldImageEditStepperComponent;
  let fixture: ComponentFixture<FormlyFieldImageEditStepperComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [FormlyFieldImageEditStepperComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FormlyFieldImageEditStepperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});

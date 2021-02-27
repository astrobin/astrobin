import { ComponentFixture, TestBed } from "@angular/core/testing";

import { FormlyFieldNgSelectComponent } from "./formly-field-ng-select.component";

describe("FormlyFieldNgSelectComponent", () => {
  let component: FormlyFieldNgSelectComponent;
  let fixture: ComponentFixture<FormlyFieldNgSelectComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FormlyFieldNgSelectComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FormlyFieldNgSelectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});

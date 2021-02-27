import { ComponentFixture, TestBed } from "@angular/core/testing";

import { initialState } from "@app/store/state";
import { IotdModule } from "@features/iotd/iotd.module";
import { provideMockStore } from "@ngrx/store/testing";
import { ImageGenerator } from "@shared/generators/image.generator";
import { MockBuilder } from "ng-mocks";
import { SubmissionEntryComponent } from "./submission-entry.component";

describe("SubmissionEntryComponent", () => {
  let component: SubmissionEntryComponent;
  let fixture: ComponentFixture<SubmissionEntryComponent>;

  beforeEach(async () => {
    await MockBuilder(SubmissionEntryComponent, IotdModule).provide(provideMockStore({ initialState }));
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SubmissionEntryComponent);
    component = fixture.componentInstance;
    component.entry = ImageGenerator.image();
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});

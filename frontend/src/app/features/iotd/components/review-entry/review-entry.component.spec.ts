import { ComponentFixture, TestBed } from "@angular/core/testing";

import { initialState } from "@app/store/state";
import { IotdModule } from "@features/iotd/iotd.module";
import { provideMockStore } from "@ngrx/store/testing";
import { ImageGenerator } from "@shared/generators/image.generator";
import { MockBuilder } from "ng-mocks";
import { ReviewEntryComponent } from "./review-entry.component";

describe("ReviewEntryComponent", () => {
  let component: ReviewEntryComponent;
  let fixture: ComponentFixture<ReviewEntryComponent>;

  beforeEach(async () => {
    await MockBuilder(ReviewEntryComponent, IotdModule).provide(provideMockStore({ initialState }));
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ReviewEntryComponent);
    component = fixture.componentInstance;
    component.entry = ImageGenerator.image();
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});

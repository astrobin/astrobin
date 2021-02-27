import { ComponentFixture, TestBed } from "@angular/core/testing";
import { initialState } from "@app/store/state";
import { IotdModule } from "@features/iotd/iotd.module";
import { provideMockStore } from "@ngrx/store/testing";
import { MockBuilder } from "ng-mocks";
import { ReviewSlotsComponent } from "./review-slots.component";

describe("ReviewSlotsComponent", () => {
  let component: ReviewSlotsComponent;
  let fixture: ComponentFixture<ReviewSlotsComponent>;

  beforeEach(
    async () => await MockBuilder(ReviewSlotsComponent, IotdModule).provide(provideMockStore({ initialState }))
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(ReviewSlotsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});

import { ComponentFixture, TestBed } from "@angular/core/testing";

import { AppModule } from "@app/app.module";
import { initialState } from "@app/store/state";
import { provideMockStore } from "@ngrx/store/testing";
import { MockBuilder } from "ng-mocks";
import { SubmissionQueueComponent } from "./submission-queue.component";

describe("SubmissionQueueComponent", () => {
  let component: SubmissionQueueComponent;
  let fixture: ComponentFixture<SubmissionQueueComponent>;

  beforeEach(async () => {
    await MockBuilder(SubmissionQueueComponent, AppModule).provide(provideMockStore({ initialState }));
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SubmissionQueueComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it("should create", () => {
    expect(component).toBeTruthy();
  });
});

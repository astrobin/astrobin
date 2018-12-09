import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { of } from "rxjs";
import { CommonApiService } from "./api/common-api.service";

import { AppContextService } from './app-context.service';

class MockCommonApiService {
  getUser = jasmine.createSpy('getUser').and.returnValue(of({id: 1}));
  getCurrentUserProfile = jasmine.createSpy('getCurrentUserProfile').and.returnValue(of({user: 1}));
  getSubscriptions = jasmine.createSpy('getSubscriptions').and.returnValue(of([]));
}

describe('AppContextService', () => {
  let service: AppContextService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        {provide: CommonApiService, useClass: MockCommonApiService}
      ]
    });
    service = TestBed.get(AppContextService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('currentUserProfile should be available',() => {
    service.load().then((response) => {
      expect(response.get().currentUserProfile.user).toEqual(1);
    });
  });

  it('currentUser should be available',() => {
    service.load().then((response) => {
      expect(response.get().currentUser.id).toEqual(1);
    });
  });
});

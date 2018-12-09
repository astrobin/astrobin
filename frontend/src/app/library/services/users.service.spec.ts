import { HttpClientTestingModule } from "@angular/common/http/testing";
import { TestBed } from '@angular/core/testing';
import { UserProfileModel } from "../models/common/userprofile.model";
import { UserSubscriptionModel } from "../models/common/usersubscription.model";
import { AppContextService } from "./app-context.service";

import { UsersService } from './users.service';

class MockAppContextService {
  get = jasmine.createSpy("get").and.returnValue({
    subscriptions: [
      {
        id: 1,
        category: "rawdata"
      }
    ]
  })
}

describe('UsersService', () => {
  let service: UsersService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule
      ],
      providers: [
        {
          provide: AppContextService,
          useClass: MockAppContextService
        }
      ]
    });

    service = TestBed.get(UsersService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should match correctly', () => {
    const mockUser = new UserProfileModel({
      userSubscriptionObjects: [
        new UserSubscriptionModel({
          id: 1,
          subscription: 1,
          valid: true
        })
      ]
    });
    expect(service.hasValidRawDataSubscription(mockUser)).toBe(true);
  });

  it('should not match an invalid one', () => {
    const mockUser = new UserProfileModel({
      userSubscriptionObjects: [
        new UserSubscriptionModel({
          id: 1,
          subscription: 1,
          valid: false
        })
      ]
    });
    expect(service.hasValidRawDataSubscription(mockUser)).toBe(false);
  });

  it('should not match it user has none', () => {
    const mockUser = new UserProfileModel();
    expect(service.hasValidRawDataSubscription(mockUser)).toBe(false);
  });
});

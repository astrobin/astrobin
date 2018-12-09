import { TestBed } from '@angular/core/testing';

import { LegacyRoutesService } from './legacy-routes.service';

describe('LegacyRoutesService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: LegacyRoutesService = TestBed.get(LegacyRoutesService);
    expect(service).toBeTruthy();
  });
});

import math
from decimal import Decimal, getcontext
from typing import Union, List, Dict, Any, Optional
from agno.tools import Toolkit

# Set high precision for financial calculations
getcontext().prec = 28

class MathTools(Toolkit):
    """
    Toolkit for precise mathematical operations used in financial modeling.
    Uses Decimal for high precision financial calculations.
    """
    
    def __init__(self):
        super().__init__(name="math_tools")
        # Register all the functions
        self.register(self.multiply)
        self.register(self.divide)
        self.register(self.add)
        self.register(self.subtract)
        self.register(self.percentage)
        self.register(self.percentage_of)
        self.register(self.compound_interest)
        self.register(self.calculate_hourly_revenue)
        self.register(self.calculate_annual_revenue)
        self.register(self.calculate_yield)
    
    @staticmethod
    def to_decimal(value: Union[float, int, str, Decimal]) -> Decimal:
        """Convert a value to Decimal for precision calculations"""
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    
    def multiply(self,
                a: Union[float, int, str, Decimal], 
                b: Union[float, int, str, Decimal]) -> str:
        """
        Multiply two numbers with high precision
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The product of a and b as a string
        """
        result = self.to_decimal(a) * self.to_decimal(b)
        return str(result)
    
    def divide(self,
              a: Union[float, int, str, Decimal], 
              b: Union[float, int, str, Decimal]) -> str:
        """
        Divide two numbers with high precision
        
        Args:
            a: Numerator
            b: Denominator
            
        Returns:
            The quotient of a and b as a string
        """
        if self.to_decimal(b) == Decimal('0'):
            raise ZeroDivisionError("Cannot divide by zero")
        result = self.to_decimal(a) / self.to_decimal(b)
        return str(result)
    
    def add(self,
           a: Union[float, int, str, Decimal], 
           b: Union[float, int, str, Decimal]) -> str:
        """
        Add two numbers with high precision
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The sum of a and b as a string
        """
        result = self.to_decimal(a) + self.to_decimal(b)
        return str(result)
    
    def subtract(self,
                a: Union[float, int, str, Decimal], 
                b: Union[float, int, str, Decimal]) -> str:
        """
        Subtract b from a with high precision
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The difference (a - b) as a string
        """
        result = self.to_decimal(a) - self.to_decimal(b)
        return str(result)
    
    def percentage(self,
                  value: Union[float, int, str, Decimal], 
                  percentage: Union[float, int, str, Decimal]) -> str:
        """
        Calculate percentage of a value
        
        Args:
            value: The base value
            percentage: The percentage to calculate
            
        Returns:
            The percentage of the value as a string
        """
        decimal_percentage = self.to_decimal(percentage)
        decimal_value = self.to_decimal(value)
        decimal_100 = self.to_decimal(100)
        
        result = decimal_value * (decimal_percentage / decimal_100)
        return str(result)
    
    def percentage_of(self,
                     part: Union[float, int, str, Decimal], 
                     whole: Union[float, int, str, Decimal]) -> str:
        """
        Calculate what percentage part is of whole
        
        Args:
            part: The part value
            whole: The whole value
            
        Returns:
            The percentage as a string
        """
        decimal_part = self.to_decimal(part)
        decimal_whole = self.to_decimal(whole)
        decimal_100 = self.to_decimal(100)
        
        result = (decimal_part / decimal_whole) * decimal_100
        return str(result)
    
    def compound_interest(self,
                         principal: Union[float, int, str, Decimal], 
                         rate: Union[float, int, str, Decimal], 
                         time: Union[float, int, str, Decimal],
                         periods: int = 1) -> str:
        """
        Calculate compound interest
        
        Args:
            principal: Initial amount
            rate: Interest rate (as a decimal, e.g., 0.05 for 5%)
            time: Time in years
            periods: Number of compounding periods per year
            
        Returns:
            Final amount after compound interest as a string
        """
        p = self.to_decimal(principal)
        r = self.to_decimal(rate)
        t = self.to_decimal(time)
        n = self.to_decimal(periods)
        
        # A = P(1 + r/n)^(nt)
        exponent = n * t
        base = Decimal('1') + (r / n)
        result = p * (base ** exponent)
        
        return str(result)
    
    def calculate_hourly_revenue(self,
                                tokens_per_second: Union[float, int, str, Decimal], 
                                price_per_million: Union[float, int, str, Decimal],
                                concurrent_requests: Union[float, int, str, Decimal] = 1) -> str:
        """
        Calculate hourly revenue from token processing
        
        Args:
            tokens_per_second: Number of tokens processed per second per request
            price_per_million: Price per million tokens
            concurrent_requests: Number of concurrent requests that can be handled
            
        Returns:
            Hourly revenue as a string
        """
        # Convert all inputs to Decimal
        tps = self.to_decimal(tokens_per_second)
        ppm = self.to_decimal(price_per_million)
        concur = self.to_decimal(concurrent_requests)
        
        # Total tokens per second with concurrency
        total_tokens_per_second = tps * concur
        
        # Convert tokens per second to tokens per hour (3600 seconds in an hour)
        tokens_per_hour = total_tokens_per_second * Decimal('3600')
        
        # Convert to millions
        millions_per_hour = tokens_per_hour / Decimal('1000000')
        
        # Calculate revenue
        result = millions_per_hour * ppm
        
        return str(result)
    
    def calculate_annual_revenue(self,
                               hourly_revenue: Union[float, int, str, Decimal], 
                               utilization_rate: Union[float, int, str, Decimal] = 100) -> str:
        """
        Calculate annual revenue from hourly revenue
        
        Args:
            hourly_revenue: Revenue per hour
            utilization_rate: Percentage of capacity utilized (default: 100)
            
        Returns:
            Annual revenue as a string
        """
        # Convert inputs to Decimal
        hr = self.to_decimal(hourly_revenue)
        ur = self.to_decimal(utilization_rate)
        
        # Calculate effective hourly revenue with utilization rate
        effective_hourly_revenue = hr * (ur / Decimal('100'))
        
        # Calculate annual revenue (24 hours per day, 365 days per year)
        result = effective_hourly_revenue * Decimal('24') * Decimal('365')
        
        return str(result)
    
    def calculate_yield(self,
                       annual_income: Union[float, int, str, Decimal], 
                       investment: Union[float, int, str, Decimal]) -> str:
        """
        Calculate yield percentage
        
        Args:
            annual_income: Annual income
            investment: Initial investment
            
        Returns:
            Yield as a percentage string
        """
        ai = self.to_decimal(annual_income)
        inv = self.to_decimal(investment)
        
        # Calculate yield as percentage
        result = (ai / inv) * Decimal('100')
        
        return str(result) 